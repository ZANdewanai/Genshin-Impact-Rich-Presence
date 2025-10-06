def update_focus_function():
    # Read the main.py file
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the new function content
    new_function = '''def is_game_focused() -> bool:
    """
    Check if the Genshin Impact game window is currently focused.
    Returns True only if the actual game window is focused, False otherwise.
    """
    from window_utils import is_genshin_window_focused
    return is_genshin_window_focused(DEBUG_MODE)'''
    
    # Find the start and end of the old function
    start = content.find('def is_game_focused() -> bool:')
    if start == -1:
        print("Could not find is_game_focused function in main.py")
        return
        
    # Find the end of the function (next function or end of file)
    next_def = content.find('def ', start + 1)
    if next_def == -1:
        next_def = len(content)
        
    # Replace the function
    new_content = content[:start] + new_function + '\n\n' + content[next_def:]
    
    # Write the updated content back to the file
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully updated the is_game_focused function in main.py")

if __name__ == "__main__":
    update_focus_function()
