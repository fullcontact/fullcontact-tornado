# FullContact V3 API Client for Python's Tornado Web Server

A library for building web applications in Python that integrate with [FullContact V3 API](https://api.fullcontact.com/v3/docs/).

## Installation

```
pip install --upgrade git+ssh://git@github.com/fullcontact/fullcontact-tornado.git
```

## Getting Started

See the [example app](/example). To run it, you must first :

1. Register a new application with FullContact via [https://beta.fullcontact.com/apps](https://beta.fullcontact.com/apps). Set the Redirect URI to point to your auth handler (http://localhost:8080/login when you run it locally).

2. Copy the "Client ID" and "Client Secret" to a new file example/config.py:

  ```python
  fullcontact_client_id = '...'
  fullcontact_client_secret = '...'
  ```

3. Run the program and go to [http://localhost:8080](http://localhost:8080) in your browser:

  ```
  python main.py
  ```
