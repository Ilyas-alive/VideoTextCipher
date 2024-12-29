import random
import os
import json
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip
import cv2

# Load configuration
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

def convert_key_to_numbers(key):
    return [int(digit) for digit in key]

key_sequence = convert_key_to_numbers(config["key"])

current_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(current_dir, exist_ok=True)

charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "

def char_to_bin(char):
    return f"{ord(char):08b}"

def bin_to_char(binary):
    return chr(int(binary, 2))

def create_random_filename(ext):
    return os.path.join(current_dir, f"{random.randint(1000, 9999)}.{ext}")

def shuffle_bits(bits):
    scrambled = ["0"] * 8
    for i, k in enumerate(key_sequence):
        scrambled[k % 8] = bits[i]
    return "".join(scrambled)

def unshuffle_bits(bits):
    unscrambled = ["0"] * 8
    for i, k in enumerate(key_sequence):
        unscrambled[i] = bits[k % 8]
    return "".join(unscrambled)

def encode_text_to_video(text, fps=128):
    if not text:
        print("Error: The input text is empty.")
        return

    output_path = create_random_filename("mp4")
    frame_size = (16, 16)
    duration = (len(text) * 8) / float(fps)

    def generate_frame(t):
        if t >= duration:
            return np.zeros((frame_size[0], frame_size[1], 3), dtype=np.uint8)

        frame_index = int(t * fps)
        overall_bit_index = frame_index % (len(text) * 8)

        char_index = overall_bit_index // 8
        bit_in_char = overall_bit_index % 8

        if char_index >= len(text):
            return np.zeros((frame_size[0], frame_size[1], 3), dtype=np.uint8)

        char = text[char_index]
        binary_rep = char_to_bin(char)
        scrambled_bits = shuffle_bits(binary_rep)
        bit = scrambled_bits[bit_in_char]

        frame = np.zeros((frame_size[0], frame_size[1], 3), dtype=np.uint8)
        color = 255 if bit == '1' else 0
        frame[:, :] = color
        return frame

    video = VideoClip(generate_frame, duration=duration)
    video.write_videofile(output_path, fps=fps, codec="libx264")
    print(f"Video saved as {output_path}")

def decode_video_to_text(video_path):
    if video_path.startswith('"') and video_path.endswith('"'):
        video_path = video_path[1:-1]

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return

    decoded_text = ""
    binary_buffer = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        avg_color = np.mean(frame)
        bit_value = '1' if avg_color >= 128 else '0'
        binary_buffer += bit_value

        if len(binary_buffer) == 8:
            try:
                unscrambled = unshuffle_bits(binary_buffer)
                decoded_text += bin_to_char(unscrambled)
            except ValueError:
                print(f"Invalid binary sequence: {binary_buffer}")
            binary_buffer = ""

    cap.release()

    if not decoded_text:
        print("Error: No text was decoded from the video.")
        return

    print(f"Decoded text: {decoded_text}")
    output_text_path = create_random_filename("txt")
    with open(output_text_path, "w", encoding="utf-8") as f:
        f.write(decoded_text)
    print(f"Decoded text saved as {output_text_path}")

if __name__ == "__main__":
    while True:
        print("Choose an option:")
        print("1. Text-to-Video Encoding")
        print("2. Video-to-Text Decoding")
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            text = input("Enter the text to encode into a video: ").strip()
            if text:
                encode_text_to_video(text)
            else:
                print("You must enter some text!")
        elif choice == "2":
            video_path = input("Enter the path to the video file: ").strip()
            decode_video_to_text(video_path)
        else:
            print("Invalid choice. Please enter 1 or 2.")

        cont = input("Do you want to perform another operation? (yes/no): ").strip().lower()
        if cont != "yes":
            break
