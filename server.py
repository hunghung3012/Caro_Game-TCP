import socket
import threading

# Server configuration
HOST = '192.168.1.4'
PORT = 12345

clients = []
roles = ['X', 'O']

def handle_client(client_socket, client_address, role):
    client_socket.send(role.encode())  # Send role (X or O) to the client
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            # Relay move or chat message to the other client
            for client in clients:
                if client != client_socket:
                    client.send(message.encode())
        except:
            break
    client_socket.close()
    clients.remove(client_socket)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    for i in range(2):
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}, assigned role {roles[i]}")
        clients.append(client_socket)
        
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, roles[i]))
        client_thread.start()

if __name__ == "__main__":
    start_server()
