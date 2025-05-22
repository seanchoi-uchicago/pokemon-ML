import tkinter as tk

def main():
    # Create the main window
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    root.configure(bg="black")  # Set window background to black
    
    # Create a frame with white background
    main_frame = tk.Frame(root, bg="white", width=380, height=280)
    main_frame.place(x=10, y=10)
    
    # Create a label with black text
    label = tk.Label(main_frame, 
                    text="Test Label", 
                    bg="white", 
                    fg="black",
                    font=("Arial", 14))
    label.place(x=150, y=50)
    
    # Create a button with gray background
    button = tk.Button(main_frame, 
                      text="Test Button",
                      bg="gray",
                      fg="white",
                      width=10,
                      height=2)
    button.place(x=150, y=100)
    
    # Create a colored rectangle
    canvas = tk.Canvas(main_frame, width=200, height=100, bg="lightblue")
    canvas.place(x=90, y=150)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main() 