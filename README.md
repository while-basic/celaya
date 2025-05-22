<div align="center">
  <a href="https://celayasolutions.com">
    <img alt="celaya" height="200px" src="https://github.com/celaya/celaya/assets/3325447/0d0b44e2-8f4a-4e99-9b52-a5c1c741c8f7">
  </a>
</div>

# Celaya

Get up and running with large language models.

### macOS

[Download](https://celayasolutions.com/download/Celaya-darwin.zip)

### Windows

[Download](https://celayasolutions.com/download/CelayaSetup.exe)

### Linux

```shell
curl -fsSL https://celayasolutions.com/install.sh | sh
```

[Manual install instructions](https://github.com/celaya/celaya/blob/main/docs/linux.md)

### Docker

The official [Celaya Docker image](https://hub.docker.com/r/celaya/celaya) `celaya/celaya` is available on Docker Hub.

### Libraries

- [celaya-python](https://github.com/celaya/celaya-python)
- [celaya-js](https://github.com/celaya/celaya-js)

### Community

- [Discord](https://discord.gg/celaya)
- [Reddit](https://reddit.com/r/celaya)

## Quickstart

To run and chat with [Llama 3.2](https://celayasolutions.com/library/llama3.2):

```shell
celaya run llama3.2
```

## Model library

Celaya supports a list of models available on [celayasolutions.com/library](https://celayasolutions.com/library 'celaya model library')

Here are some example models that can be downloaded:

| Model              | Parameters | Size  | Download                         |
| ------------------ | ---------- | ----- | -------------------------------- |
| Gemma 3            | 1B         | 815MB | `celaya run gemma3:1b`           |
| Gemma 3            | 4B         | 3.3GB | `celaya run gemma3`              |
| Gemma 3            | 12B        | 8.1GB | `celaya run gemma3:12b`          |
| Gemma 3            | 27B        | 17GB  | `celaya run gemma3:27b`          |
| QwQ                | 32B        | 20GB  | `celaya run qwq`                 |
| DeepSeek-R1        | 7B         | 4.7GB | `celaya run deepseek-r1`         |
| DeepSeek-R1        | 671B       | 404GB | `celaya run deepseek-r1:671b`    |
| Llama 4            | 109B       | 67GB  | `celaya run llama4:scout`        |
| Llama 4            | 400B       | 245GB | `celaya run llama4:maverick`     |
| Llama 3.3          | 70B        | 43GB  | `celaya run llama3.3`            |
| Llama 3.2          | 3B         | 2.0GB | `celaya run llama3.2`            |
| Llama 3.2          | 1B         | 1.3GB | `celaya run llama3.2:1b`         |
| Llama 3.2 Vision   | 11B        | 7.9GB | `celaya run llama3.2-vision`     |
| Llama 3.2 Vision   | 90B        | 55GB  | `celaya run llama3.2-vision:90b` |
| Llama 3.1          | 8B         | 4.7GB | `celaya run llama3.1`            |
| Llama 3.1          | 405B       | 231GB | `celaya run llama3.1:405b`       |
| Phi 4              | 14B        | 9.1GB | `celaya run phi4`                |
| Phi 4 Mini         | 3.8B       | 2.5GB | `celaya run phi4-mini`           |
| Mistral            | 7B         | 4.1GB | `celaya run mistral`             |
| Moondream 2        | 1.4B       | 829MB | `celaya run moondream`           |
| Neural Chat        | 7B         | 4.1GB | `celaya run neural-chat`         |
| Starling           | 7B         | 4.1GB | `celaya run starling-lm`         |
| Code Llama         | 7B         | 3.8GB | `celaya run codellama`           |
| Llama 2 Uncensored | 7B         | 3.8GB | `celaya run llama2-uncensored`   |
| LLaVA              | 7B         | 4.5GB | `celaya run llava`               |
| Granite-3.3         | 8B         | 4.9GB | `celaya run granite3.3`          |

> [!NOTE]
> You should have at least 8 GB of RAM available to run the 7B models, 16 GB to run the 13B models, and 32 GB to run the 33B models.

## Customize a model

### Import from GGUF

Celaya supports importing GGUF models in the Modelfile:

1. Create a file named `Modelfile`, with a `FROM` instruction with the local filepath to the model you want to import.

   ```
   FROM ./vicuna-33b.Q4_0.gguf
   ```

2. Create the model in Celaya

   ```shell
   celaya create example -f Modelfile
   ```

3. Run the model

   ```shell
   celaya run example
   ```

### Import from Safetensors

See the [guide](docs/import.md) on importing models for more information.

### Customize a prompt

Models from the Celaya library can be customized with a prompt. For example, to customize the `llama3.2` model:

```shell
celaya pull llama3.2
```

Create a `Modelfile`:

```
FROM llama3.2

# set the temperature to 1 [higher is more creative, lower is more coherent]
PARAMETER temperature 1

# set the system message
SYSTEM """
You are Mario from Super Mario Bros. Answer as Mario, the assistant, only.
"""
```

Next, create and run the model:

```
celaya create mario -f ./Modelfile
celaya run mario
>>> hi
Hello! It's your friend Mario.
```

For more information on working with a Modelfile, see the [Modelfile](docs/modelfile.md) documentation.

## CLI Reference

### Create a model

`celaya create` is used to create a model from a Modelfile.

```shell
celaya create mymodel -f ./Modelfile
```

### Pull a model

```shell
celaya pull llama3.2
```

> This command can also be used to update a local model. Only the diff will be pulled.

### Remove a model

```shell
celaya rm llama3.2
```

### Copy a model

```shell
celaya cp llama3.2 my-model
```

### Multiline input

For multiline input, you can wrap text with `"""`:

```
>>> """Hello,
... world!
... """
I'm a basic program that prints the famous "Hello, world!" message to the console.
```

### Multimodal models

```
celaya run llava "What's in this image? /Users/jmorgan/Desktop/smile.png"
```

> **Output**: The image features a yellow smiley face, which is likely the central focus of the picture.

### Pass the prompt as an argument

```shell
celaya run llama3.2 "Summarize this file: $(cat README.md)"
```

> **Output**: Celaya is a lightweight, extensible framework for building and running language models on the local machine. It provides a simple API for creating, running, and managing models, as well as a library of pre-built models that can be easily used in a variety of applications.

### Show model information

```shell
celaya show llama3.2
```

### List models on your computer

```shell
celaya list
```

### List which models are currently loaded

```shell
celaya ps
```

### Stop a model which is currently running

```shell
celaya stop llama3.2
```

### Start Celaya

`celaya serve` is used when you want to start celaya without running the desktop application.

## Building

See the [developer guide](https://github.com/celaya/celaya/blob/main/docs/development.md)

### Running local builds

Next, start the server:

```shell
./celaya serve
```

Finally, in a separate shell, run a model:

```shell
./celaya run llama3.2
```

## REST API

Celaya has a REST API for running and managing models.

### Generate a response

```shell
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt":"Why is the sky blue?"
}'
```

### Chat with a model

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    { "role": "user", "content": "why is the sky blue?" }
  ]
}'
```

See the [API documentation](./docs/api.md) for all endpoints.
