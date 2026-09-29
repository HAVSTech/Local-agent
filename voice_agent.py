import json
import sys
import time
import wave
from pathlib import Path

import numpy as np
import pyttsx3
import sounddevice as sd
from faster_whisper import WhisperModel

from print_agent.executor import PrintExecutor
from print_agent.file_manager import FileManager
from print_agent.llm import OllamaPlanner


class LocalVoiceAgent:
    def __init__(self, config_path="config.json"):
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.sample_rate = int(cfg.get("voice_sample_rate", 16000))
        self.max_record_seconds = float(cfg.get("voice_max_record_seconds", 15))
        self.silence_seconds = float(cfg.get("voice_silence_seconds", 1.4))
        self.silence_threshold = float(cfg.get("voice_silence_threshold", 0.012))
        self.wav_path = Path(cfg.get("voice_temp_wav", ".voice_input.wav"))

        model_name = cfg.get("voice_stt_model", "tiny.en")
        device = cfg.get("voice_stt_device", "cpu")
        compute_type = cfg.get("voice_stt_compute_type", "int8")
        print(f"Loading local Whisper model: {model_name}")
        self.stt = WhisperModel(model_name, device=device, compute_type=compute_type)

        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", int(cfg.get("voice_tts_rate", 175)))

        self.planner = OllamaPlanner(
            cfg["ollama_url"], cfg["model"], cfg.get("llm_timeout_seconds", 120)
        )
        self.fm = FileManager(
            cfg["allowed_roots"], cfg.get("max_files_per_job", 100)
        )
        self.executor = PrintExecutor(
            cfg["printer_name"], cfg.get("spool_wait_seconds", 120)
        )

    def speak(self, text):
        print(f"Agent: {text}")
        self.tts.say(text)
        self.tts.runAndWait()

    def record(self):
        print("Listening... speak now.")
        block = 0.1
        frames = []
        started = False
        silent_for = 0.0
        start_time = time.monotonic()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=int(self.sample_rate * block),
        ) as stream:
            while time.monotonic() - start_time < self.max_record_seconds:
                data, _ = stream.read(int(self.sample_rate * block))
                chunk = data[:, 0].copy()
                frames.append(chunk)
                rms = float(np.sqrt(np.mean(np.square(chunk))) + 1e-12)

                if rms >= self.silence_threshold:
                    started = True
                    silent_for = 0.0
                elif started:
                    silent_for += block
                    if silent_for >= self.silence_seconds:
                        break

        audio = np.concatenate(frames) if frames else np.array([], dtype=np.float32)
        if audio.size == 0 or not started:
            return ""

        with wave.open(str(self.wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            pcm = np.clip(audio, -1, 1)
            wf.writeframes((pcm * 32767).astype(np.int16).tobytes())

        return str(self.wav_path)

    def transcribe(self, wav_path):
        segments, _ = self.stt.transcribe(
            wav_path,
            beam_size=1,
            language="en",
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        print(f"You: {text}")
        return text

    def handle_command(self, command):
        intent = self.planner.plan(command)
        if not intent.folder:
            self.speak("Please include a usable Windows folder path.")
            return

        files = self.fm.list_files(
            intent.folder,
            intent.extensions,
            intent.recursive,
            intent.exclude_contains,
            intent.sort_order,
        )

        if not files:
            self.speak("I couldn't find any matching files to print.")
            return

        print("\nValidated plan:")
        print(intent.model_dump_json(indent=2))
        print(f"Found {len(files)} file(s).")
        for i, path in enumerate(files, 1):
            print(f"  {i}. {path}")

        self.speak(f"I found {len(files)} matching file{'s' if len(files) != 1 else ''}.")
        self.speak("Do you want me to print them?")

        confirmation_wav = self.record()
        if not confirmation_wav:
            self.speak("I didn't hear a confirmation. Printing cancelled.")
            return

        answer = self.transcribe(confirmation_wav).lower()
        if not any(word in answer for word in ("yes", "yeah", "yep", "print", "okay", "ok", "sure", "confirm")):
            self.speak("Printing cancelled.")
            return

        self.speak("Okay. Starting the print job.")
        result = self.executor.execute(files, intent)
        completed = len(result["completed"])
        if result["failed"]:
            failed = result["failed"][0]
            self.speak(f"I printed {completed} file{'s' if completed != 1 else ''}, then the job stopped because of an error.")
            print(f"Failure: {failed}")
        else:
            self.speak(f"Done. I printed {completed} file{'s' if completed != 1 else ''} successfully.")

    def run(self):
        self.speak("Local print assistant is ready.")
        self.speak("Say a print command, then pause when you finish speaking.")

        while True:
            try:
                wav_path = self.record()
                if not wav_path:
                    continue

                command = self.transcribe(wav_path)
                if not command:
                    self.speak("I didn't catch that. Please try again.")
                    continue

                if command.lower() in {"exit", "quit", "stop", "goodbye"}:
                    self.speak("Goodbye.")
                    break

                try:
                    self.handle_command(command)
                except Exception as exc:
                    print(f"Error: {exc}")
                    self.speak("I couldn't complete that request. Please check the terminal for the error.")
            except KeyboardInterrupt:
                print()
                self.speak("Goodbye.")
                break
            except Exception as exc:
                print(f"Voice error: {exc}")
                self.speak("The microphone or voice system reported an error.")


if __name__ == "__main__":
    LocalVoiceAgent().run()
