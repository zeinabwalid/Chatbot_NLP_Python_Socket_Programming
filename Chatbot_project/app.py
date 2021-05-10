import os
from flask import Flask, render_template, request
import socket
import sys
import ssl


Sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #get instance of UDP socket
app = Flask(__name__)
app.static_folder = 'static'

#using flask to only render the html file
@app.route("/")
def home():
    return render_template("index.html")

#here we get the user input encoded and then return the reply to the user decoded  
@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    Sock.sendto(userText.encode(),("127.0.0.1",80))   #send userText to server by socket
    data,addr = Sock.recvfrom(4096)    #receive server response
    output = data.decode()   #decode server response
    return output

if __name__ == "__main__":
    app.run(debug=True,port=80)