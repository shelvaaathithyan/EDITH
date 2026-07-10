import keyboard

print("Listening for key 8...")
print("Press ESC to quit.\n")

keyboard.on_press_key("8", lambda e: print("8 PRESSED"))
keyboard.on_release_key("8", lambda e: print("8 RELEASED"))

keyboard.wait("esc")