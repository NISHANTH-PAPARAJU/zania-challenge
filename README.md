# zania-challenge
This is a Document Q&A chat bot built by using fastapi backend and a react frontend.

- The backend code lives under /backend
- The frontend code live under /frontend

## Instructions to run the application
Both the frnt end and backend are containerized using specific Dockerfiles.

The docker-compose.yaml file manifests the creation of the containers.

To start:
- Open a terminal session
- clone the repo using `git clone https://github.com/NISHANTH-PAPARAJU/zania-challenge.git`
- cd into the zenia-challenge folder
- create a `.env` file inside `backend/` folder
- Add the following env variables
    - SLACK_BOT_TOKEN: slack token of the app that is installed on the workspace
    - OPENAI_API_KEY: api key to call openai models
    - SLACK_CHANNEL_ID: slack channel id needed for the slack tool
    - OPENAI_MODEL: The model name that you want to use fropm openai
- run `docker compose up`
- This will run both the backend and frontend containers locally

The front is available by default at `localhost:3000`

## Question on the challenge:
- Ways you can make the solution more accurate
    - Due to the time constraints the current solution has some scope for improvements.
        
        1. As we know the main crux of the RAG pipeline is effective embeddings and having a `dynamic chunking` logic based on the number of pages, number of words in a page, etc. tends to do better as oposed to the current static chunking logic.
        2. The current implementation is a plain text embeddings, which might not do well with documents containing lot of images & charts. In such cases we can employ having a seperate `image extractions -> image descriptions (may be generated using llms) -> imagage embeddings`. These embeddings can be passed on to the retrieval logic to better answer the questions.
        3. The current implementation is designed for only 1 document, so extending this to a multi document Q&A with large set of tools, comes with its own challenges. Like larger retrieved context might result in context window constraints, for this we can make use of tool retrieval using `ObjectIndex` to get the relevant context.
        4. Impove the agentic behaviour by adding `step evaluations` after each step until we prompt the tools to get the right solution for the step.
        5. Some user experience enhancements like authentication, chat history & wait bars can be added.
        6. We can stream the responses which improves the user experience.
        7. Refine the prompts by providing more examples & use the few shot prompting.

- How you would have made your code more modular, scalable and production grade
    - The basic document services like for all document-related operations, such as handling file uploads, parsing, image description generator can be abstracted into document_service module
    - If we plan to use a large set of tools, these can be abstracted into a seperate tools folder.
    - We can add more effective error handlings and logging to better understand the failures
    - We can add rate limiting per user to avoid large number of requests from individual users
    - We definitely need to add unit tests, which I missed due to time constraints. 
    - I'm not a great frontend engineer, so there would definitely be some best practices in frontend to follow.
    - api endpoints coould be versioned and the api module can be seperated out of the main app.py
    - Strongly typing datatypes of the input & output parameters of all the functions.

- A video or demo of your program in action.
    - This is provided as an attachment in the email response.

