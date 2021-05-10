import random
import json
import socketserver, threading, time
import os
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


## create our chat bot processing on server 

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)
    
## read saved model 
FILE = "data.pth"
data = torch.load(FILE)
## specify input data 
input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

## get our model ready for use 
model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Bot"

## bot_out function to get the user inut and give it to our model and provide reply to server
def bot_out(sentence):
    sentence = sentence
    sentence = tokenize(sentence) ## apply tokenization 
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device) ## get our final format of user input 

    output = model(X)
    _, predicted = torch.max(output, dim=1) ## get the highst probabily of the output sentence 

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1) ## apply soft max on the output array 
    prob = probs[0][predicted.item()]
    out = ""
    ## check if this probabilty is sufficent for make reply to clint or not 
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                ## out send to web 
                out = random.choice(intent['responses'])
                out = f"{bot_name}: {out}"                
    else:
        ## chatbot out if the input word is far away from our data 
        out = f"{bot_name}: I do not understand..."
    return out
        
class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):          # handle multiple clients by threading

    def handle(self):
        data = self.request[0].strip()        # sent data from client
        sentence = data.decode("utf-8")       # decoding sent data
        print(bot_out(sentence))
        socket = self.request[1] # get instance of UDP socket       
        current_thread = threading.current_thread()      # return thread object,corresponding to the caller’s thread of control
        print("{}: client: {}, wrote: {}".format(current_thread.name, self.client_address, data))# printed on terminal
        data= bot_out(sentence)
        socket.sendto(data.encode(), self.client_address)  # send back output of NLP alg. back to client specified by address

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):#create Threaded UDP server
    pass

if __name__ == "__main__":
    HOST, PORT = "127.0.0.1",3000  # select specific IP(LocalHost) and Port
    server = ThreadedUDPServer((HOST, PORT), ThreadedUDPRequestHandler)#define interface of server object
    server_thread = threading.Thread(target=server.serve_forever) #server.serve_forever:handle requests until an explicit shutdown()
    server_thread.daemon = True # make the program finishes after the main thread is executed

    try:
        server_thread.start() # start threaded server
        print("Server started at {} port {}".format(HOST, PORT)) # printed on terminal
        while True: time.sleep(10) # hang server till any client send 
    except (KeyboardInterrupt, SystemExit): # for any errors happened
        server.shutdown() #Tell the serve_forever() loop to stop
        server.server_close() #Clean up the server                    
        exit() # exit the program



