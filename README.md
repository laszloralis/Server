# Server

## Functionality:

- the server requests the blog posts from 'https://www.thekey.academy/wp-json/wp/v2/posts'
- parses the content and counts the words
- sends the result to the connected clients via websocket protocol (on 'localhost', port 8000, without any encription)

## Files:

**main.py**

- main loop

**wordpress_io.py**

- wordpress communication to receive the posts
- searches for new/changed/deleted posts
- counts the words and stores the results

**parser_functions.py**

- parser helper functions, used by wordpress_io
  
**protocol_io.py**

- simple protocol to achieve the communication between the server and the clients

**websocket_io.py**

- used by the protocol to communicate with the clients
  
**shared_storage.py**

- a simple thread-safe storage, used by protocol_io 


## Requirements:

You will need Python interpreter (the project was developed/tested with v3.9)

You should also install a few packages:
- beautifulsoup4
- websockets
- requests
