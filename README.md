# slack-ragbot

Retrieval Augmented Generation Slack Bot - A Bolty Fork

## Overview
This repository contains a Slack bot that leverages Retrieval Augmented Generation (RAG) to provide enhanced, context-aware responses in Slack channels. Built as a fork of the Bolty project, this bot integrates with Slack and various data sources to deliver relevant, AI-powered answers to user queries.

## Features
- Slack integration for real-time Q&A
- Retrieval Augmented Generation (RAG) for improved context and accuracy
- Connects to custom or external data sources
- Modular and extensible architecture

## Getting Started

This project assumes you are operating on a Virtual Machine built by the provided Terraform. This instance has the appropriate credentials to operate the Slack bot application.

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Makersmiths/slack-ragbot.git
   cd slack-ragbot
   ```
   
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure your environment:**
   - Copy `manifest.json` and `slack.json` as needed and fill in your Slack app credentials.
   - Set up any required environment variables or configuration files as described in the documentation.

4. **Run the bot:**
   ```sh
   python slackbot/app.py
   ```

## Folder Structure
- `slackbot/` - Main bot code and configuration
- `ai/` - AI and RAG provider logic
- `infrastructure/` - Infrastructure as code and deployment scripts
- `data/`, `lib/`, `listeners/`, `state_store/` - Supporting modules and data
- `tests/` - Test suite

## License
MIT

## Acknowledgements
- Forked from [Bolty](https://github.com/bolty-ai/bolty)
- Built by Makersmiths
