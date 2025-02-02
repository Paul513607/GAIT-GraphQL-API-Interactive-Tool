<!--
Hey, thanks for using the awesome-readme-template template.  
If you have any enhancements, then fork this project and create a pull request 
or just open an issue with the label "enhancement".

Don't forget to give this project a star for additional support ;)
Maybe you can mention me or this repo in the acknowledgements too
-->
<div align="center">

  <img src="assets/logo.png" alt="logo" width="200" height="auto" />
  <h1>GAIT GraphQL API Interactive Tool</h1>
  
   
<h4>
    <a href="https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool">View Demo</a>
  <span> · </span>
    <a href="https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool">Documentation</a>
  <span> · </span>
    <a href="https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool/issues/">Report Bug</a>
  <span> · </span>
    <a href="https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool/issues/">Request Feature</a>
</h4>
</div>

<br />

<!-- Table of Contents -->
# :notebook_with_decorative_cover: Table of Contents

- [About the Project](#star2-about-the-project)
  * [Screenshots](#camera-screenshots)
  * [Tech Stack](#space_invader-tech-stack)
  * [Features](#dart-features)
  * [Environment Variables](#key-environment-variables)
- [Getting Started](#toolbox-getting-started)
  * [Prerequisites](#bangbang-prerequisites)
  * [Installation](#gear-installation)
  * [Run Locally](#running-run-locally)
- [Usage](#eyes-usage)
- [Roadmap](#compass-roadmap)
- [License](#warning-license)
- [Contact](#handshake-contact)
- [Acknowledgements](#gem-acknowledgements)

  

<!-- About the Project -->
## :star2: About the Project


<!-- Screenshots -->
### :camera: Screenshots

<div align="center"> 
  <img src="https://placehold.co/600x400?text=Your+Screenshot+here" alt="screenshot" />
</div>


<!-- TechStack -->
### :space_invader: Tech Stack

<details>
  <summary>Client</summary>
  <ul>
    <li><a href="https://www.typescriptlang.org/">Typescript</a></li>
    <li><a href="https://angularjs.org/">Angular.js</a></li>
  </ul>
</details>

<details>
  <summary>Server</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li><a href="https://flask.palletsprojects.com/en/stable/">Flask</a></li>
    <li><a href="https://wordnet.princeton.edu/">Wordnet</a></li>    
    <li><a href="https://spacy.io/">Spacy</a></li>
    <li><a href="https://openai.com/">OpenAI</a></li>
    <li><a href="https://socket.io/">SocketIO</a></li>
    <li><a href="https://graphql.org/">GraphQL</a></li>
  </ul>
</details>

<details>
<summary>DevOps</summary>
  <ul>
    <li><a href="https://www.docker.com/">Docker</a></li>
    <li><a href="https://aws.amazon.com/">AWS</a></li>
  </ul>
</details>

<!-- Features -->
### :dart: Features

- Two-way communication between client and server
- A NLP module that receives a public GraphQL API and a text and returns a GraphQL query
- A web interface that allows the user to interact with the NLP module and also with the public GraphQL API

<!-- Env Variables -->
### :key: Environment Variables

To run this project, you will need to add the following environment variables to your .env file inside the nlp-model folder

`OPENAI_API_KEY`

<!-- Getting Started -->
## 	:toolbox: Getting Started

<!-- Prerequisites -->
### :bangbang: Prerequisites

This project uses npm and angular.js. If you don't have them installed, you can install them with the following commands:

```bash
 npm install npm@latest -g
```

```bash
 npm install --global @angular/cli
```

For the backend, you will need to have python installed. You can download it [here](https://www.python.org/downloads/)

<!-- Installation -->
### :gear: Installation

Install gait-ui with npm
```bash
    cd gait-ui
    npm install
```

Install query-manager with pip
```bash
    cd query-manager
    pip install -r requirements.txt
```

Install the nlp-model with pip
```bash
    cd nlp-model
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    python -m spacy download en_core_web_md
```

<!-- Run Locally -->
### :running: Run Locally

Clone the project

```bash
  git clone https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool.git
```

Go to the project directory

```bash
  cd GAIT-GraphQL-API-Interactive-Tool
```

Install dependencies

gait-ui
```bash
  cd gait-ui
  npm install
```

query-manager
```bash
  cd query-manager
  pip install -r requirements.txt
```

nlp-model
```bash
  cd nlp-model
  pip install -r requirements.txt
  python -m spacy download en_core_web_sm
  python -m spacy download en_core_web_md
```

Start the server

gait-ui
```bash
  cd gait-ui
  ng serve
```

query-manager
```bash
  cd query-manager
  uvicorn app.py
```

nlp-model
```bash
  cd nlp-model
  python main.py
```

<!-- Usage -->
## :eyes: Usage


<!-- Roadmap -->
## :compass: Roadmap

* Improving the custom NLP model
* Support for more public GraphQL APIs
* Adding more features to the web interface


<!-- License -->
## :warning: License

Distributed under the MIT License

Copyright (c) [2025] [Samson Ioan Paul & Leahu Vlad-Iulius]

<!-- Contact -->
## :handshake: Contact

Project Link: [https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool](https://github.com/Paul513607/GAIT-GraphQL-API-Interactive-Tool)


<!-- Acknowledgments -->
## :gem: Acknowledgements
 - [University Alexandru Ioan Cuza Iasi, WADE lab](https://profs.info.uaic.ro/sabin.buraga/teach/courses/wade)
 - [OpenAI](https://openai.com/)
 - [Spacy](https://spacy.io/)
 - [GraphQL](https://graphql.org/)
 - [Angular.js](https://angularjs.org/)