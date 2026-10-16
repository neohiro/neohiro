import os

def create_godmode_folder():
    """
    Creates a 'GodMode' folder on the user's desktop.
    This folder provides shortcuts to all Windows settings.
    """
    # Define the special name for the GodMode folder.
    # The part in curly braces is a specific Windows Class Identifier (CLSID).
    folder_name = "GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}"

    # Get the path to the user's desktop directory.
    # This works for most Windows versions.
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

    # Construct the full path for the new folder.
    godmode_path = os.path.join(desktop_path, folder_name)

    # Check if the folder already exists to avoid errors.
    if not os.path.exists(godmode_path):
        try:
            # Create the directory.
            os.makedirs(godmode_path)
            print(f"GodMode folder created successfully on your desktop at: {godmode_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("GodMode folder already exists on your desktop. No action needed.")

if __name__ == "__main__":
    create_godmode_folder()

