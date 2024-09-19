import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font

HOST = '192.168.1.4'
PORT = 12345

class CaroGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Caro Game")
        self.connection = None
        self.my_turn = False
        self.role = None  # Role will be X or O

        self.font_style = Font(family="Permanent Marker", weight="bold")
        # Create Connect button
        self.connect_button = tk.Button(root, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        # Create 10x10 grid of buttons for the board
        self.board_frame = tk.Frame(root)
        self.board_frame.pack()

        self.buttons = []
        self.board = [['' for _ in range(10)] for _ in range(10)]  # Logic representation of the board
        for row in range(10):
            button_row = []
            for col in range(10):
                button = tk.Button(self.board_frame, text='', width=4, height=2, font=self.font_style,bg='#FFFFFF',command=lambda r=row, c=col: self.make_move(r, c), relief=tk.RAISED, border=1)
                button.grid(row=row, column=col)
                button.bind("<Enter>", self.on_enter)
                button.bind("<Leave>", self.on_leave)
                button_row.append(button)
            self.buttons.append(button_row)

        # Create chat area
        self.chat_frame = tk.Frame(root)
        self.chat_frame.pack(pady=10)

        self.chat_log = tk.Text(self.chat_frame, width=50, height=10, state=tk.DISABLED)
        self.chat_log.pack(side=tk.LEFT)

        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_log.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.config(yscrollcommand=self.scrollbar.set)

        # Input field for message
        self.message_entry = tk.Entry(root, width=40)
        self.message_entry.pack(pady=5)

        # Button to send message
        self.send_button = tk.Button(root, text="Send Message", command=self.send_message)
        self.send_button.pack()

    def connect_to_server(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((HOST, PORT))
            threading.Thread(target=self.receive_role, daemon=True).start()  # Receive the role (X or O)
            self.connect_button.config(state=tk.DISABLED)
        except:
            messagebox.showerror("Connection Failed", "Unable to connect to the server.")

    def receive_role(self):
        self.role = self.connection.recv(1024).decode()  # Receive role from server
        if self.role == 'X':
            self.my_turn = True  # X always starts first
        messagebox.showinfo("Role Assigned", f"You are playing as {self.role}")
        threading.Thread(target=self.receive_message, daemon=True).start()

    def make_move(self, row, col):
        if self.my_turn and not self.buttons[row][col]['text']:
            color = 'red' if self.role == 'X' else 'blue'
            self.buttons[row][col].config(text=self.role, fg = color)
            self.board[row][col] = self.role  # Update logic board

            if self.check_win(row, col, self.role):
                self.send_move(row, col)  # Send the final move
                self.send_win_message()  # Send win notification to the server
            else:
                self.send_move(row, col)
            self.my_turn = False

    def send_win_message(self):
        if self.connection:
            win_message = f"WIN,{self.role}"
            self.connection.send(win_message.encode())

    def send_move(self, row, col):
        if self.connection:
            move = f"MOVE,{row},{col}"
            self.connection.send(move.encode())

    def send_message(self):
        message = self.message_entry.get()
        if message and self.connection:
            self.chat_log.config(state=tk.NORMAL)
            self.chat_log.insert(tk.END, f"You: {message}\n")
            self.chat_log.config(state=tk.DISABLED)
            self.connection.send(f"CHAT,{message}".encode())
            self.message_entry.delete(0, tk.END)

    def receive_message(self):
     
        while True:
            try:
                message = self.connection.recv(1024).decode()
                if not message:
                    break

                if message.startswith("MOVE"):
                    _, row, col = message.split(',')
                    row, col = int(row), int(col)
                    opponent_role = 'O' if self.role == 'X' else 'X'  # Opponent's role

                    # set color
                    color = 'blue' if opponent_role == 'O' else 'red'
                    self.buttons[row][col].config(text=opponent_role, fg = color)  # Opponent's move
                    self.board[row][col] = opponent_role  # Update logic board
                    self.my_turn = True  # Switch turn
                    

                elif message.startswith("WIN"):
                    # print(message)
                   
                    _, winner = message.split(',')
                    
                
                    if winner == self.role:
                            messagebox.showinfo("Game Over", "You win!")
                    else:
                            messagebox.showinfo("Game Over", "You lose!")
                    
                    self.reset_game()

                  

                elif message.startswith("CHAT"):
                    _, chat_message = message.split(',', 1)
                    self.chat_log.config(state=tk.NORMAL)
                    self.chat_log.insert(tk.END, f"Opponent: {chat_message}\n")
                    self.chat_log.config(state=tk.DISABLED)
            except:
                break

    def check_win(self, row, col, player):
        # Check row, column, diagonal and anti-diagonal
        count = 0
        for c in range(10):
            if self.board[row][c] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0

        count = 0
        for r in range(10):
            if self.board[r][col] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0

        count = 0
        start_row, start_col = row, col
        while start_row > 0 and start_col > 0:
            start_row -= 1
            start_col -= 1
        while start_row < 10 and start_col < 10:
            if self.board[start_row][start_col] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0
            start_row += 1
            start_col += 1

        count = 0
        start_row, start_col = row, col
        while start_row > 0 and start_col < 9:
            start_row -= 1
            start_col += 1
        while start_row < 10 and start_col >= 0:
            if self.board[start_row][start_col] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0
            start_row += 1
            start_col -= 1

        return False

    def reset_game(self):
        for row in range(10):
            for col in range(10):
                self.buttons[row][col].config(text='')
                self.board[row][col] = ''
    def on_enter(self, event):
       event.widget.config(bg='#FBE8A4')

    def on_leave(self, event):
        event.widget.config(bg='#FFFFFF')

if __name__ == "__main__":
    root = tk.Tk()
    game = CaroGame(root)
    root.geometry("800x990")
    root.mainloop()
