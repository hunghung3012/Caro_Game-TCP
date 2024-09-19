import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font

HOST = '192.168.1.4'
PORT = 12345

class CaroGame:
    def __init__(self, root, board_size=10):
        self.root = root
        self.root.title("Caro Game")
        self.connection = None
        self.my_turn = False
        self.role = None  # Role will be X or O
        self.color_label = "#737373"  # Role will be X or O

        self.board_size = board_size  # Add board_size parameter

        self.font_style = Font(family="Permanent Marker", weight="bold")
        self.label_font = Font(family="Permanent Marker", size=10)  # Font for labels

        # Tạo frame chứa bàn cờ và chat
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=10, pady=10)

        # Tạo frame chứa chat và nút gửi
        self.chat_frame = tk.Frame(self.main_frame)
        self.chat_frame.pack(side=tk.LEFT, padx=10)

        # Tạo nút Connect ở phía trên cùng
        self.connect_button = tk.Button(self.chat_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        # Tạo khung chat và tin nhắn
        self.chat_log = tk.Text(self.chat_frame, width=30, height=15, state=tk.DISABLED)
        self.chat_log.pack(pady=5)

        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_log.yview, background='#c9c9c9')
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.config(yscrollcommand=self.scrollbar.set)

        self.message_entry = tk.Entry(self.chat_frame, width=30)
        self.message_entry.pack(pady=5)

        self.send_button = tk.Button(self.chat_frame, text="Send Message", command=self.send_message)
        self.send_button.pack(pady=5)

        # Tạo frame chứa bàn cờ
        self.board_frame = tk.Frame(self.main_frame)
        self.board_frame.pack(side=tk.RIGHT, padx=10)

        # Tạo grid của các nút cho bàn cờ
        self.buttons = []
        self.board = [['' for _ in range(board_size)] for _ in range(board_size)]  # Logic representation of the board

        # Thêm nhãn cho cột (A, B, C, ...)
        for col in range(board_size):
            label = tk.Label(self.board_frame, text=chr(65 + col), font=self.label_font, fg=self.color_label, bg=self.board_frame.cget("bg"))
            label.grid(row=0, column=col + 1, padx=1, pady=1)

        # Thêm nhãn cho hàng (1, 2, 3, ...)
        for row in range(board_size):
            label = tk.Label(self.board_frame, text=str(row + 1), font=self.label_font, fg=self.color_label, bg=self.board_frame.cget("bg"))
            label.grid(row=row + 1, column=0, padx=1, pady=1)

        for row in range(board_size):
            button_row = []
            for col in range(board_size):
                frame = tk.Frame(self.board_frame, bg='#FFFFFF', bd=1)  # Frame with black border
                frame.grid(row=row + 1, column=col + 1, padx=1, pady=1)  # Add some padding to create space for the border
                button = tk.Button(frame, text='', width=4, height=2, font=self.font_style, bg='#FFFFFF', command=lambda r=row, c=col: self.make_move(r, c), relief=tk.FLAT)
                button.pack()
                button.bind("<Enter>", self.on_enter)
                button.bind("<Leave>", self.on_leave)
                button_row.append(button)
            self.buttons.append(button_row)

        # Tạo nhãn trạng thái lượt
        self.turn_status_font = Font(family="Inter", size=9)
        self.turn_status_label = tk.Label(self.board_frame, font=self.turn_status_font, text="Đang chờ", fg="black")
        self.turn_status_label.grid(row=board_size + 2, column=1, columnspan=board_size, pady=10)


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
        self.update_turn_status()
        messagebox.showinfo("Role Assigned", f"You are playing as {self.role}")
        threading.Thread(target=self.receive_message, daemon=True).start()

    def make_move(self, row, col):
        if self.my_turn and not self.buttons[row][col]['text']:
            color = 'red' if self.role == 'X' else 'blue'
            self.buttons[row][col].config(text=self.role, fg=color)
            self.board[row][col] = self.role  # Update logic board

            if self.check_win(row, col, self.role):
                self.send_move(row, col)  # Send the final move
                self.send_win_message()  # Send win notification to the server
            else:
                self.send_move(row, col)
            self.my_turn = False
            self.update_turn_status()

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
                    self.buttons[row][col].config(text=opponent_role, fg=color)  # Opponent's move
                    self.board[row][col] = opponent_role  # Update logic board
                    self.my_turn = True  # Switch turn
                    self.update_turn_status()

                elif message.startswith("WIN"):
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
        for c in range(self.board_size):
            if self.board[row][c] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0

        count = 0
        for r in range(self.board_size):
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
        while start_row < self.board_size and start_col < self.board_size:
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
        while start_row > 0 and start_col < self.board_size - 1:
            start_row -= 1
            start_col += 1
        while start_row < self.board_size and start_col >= 0:
            if self.board[start_row][start_col] == player:
                count += 1
                if count == 5:
                    return True
            else:
                count = 0
            start_row += 1
            start_col -= 1

        return False
    def update_turn_status(self):
        if self.my_turn:
            self.turn_status_label.config(text="Tới lượt bạn", fg="green")
        else:
            self.turn_status_label.config(text="Đang chờ lượt", fg="black")
    def reset_game(self):
        for row in range(self.board_size):
            for col in range(self.board_size):
                self.buttons[row][col].config(text='', bg='#FFFFFF')
                self.board[row][col] = ''

    def on_enter(self, event):
        event.widget.config(bg='#FBE8A4')

    def on_leave(self, event):
        event.widget.config(bg='#FFFFFF')

if __name__ == "__main__":
    root = tk.Tk()
    game = CaroGame(root, board_size=10)  # You can change the board size here
    root.geometry("1000x600")
    root.mainloop()