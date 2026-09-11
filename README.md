# Job Assistant Bot

Job Assistant Bot is an AI-powered career assistant designed to simplify the job search and application process. The system helps candidates discover relevant job opportunities, understand job requirements, evaluate how well a job matches their skills and experience, and prepare personalized application documents. The main objective of the project is to reduce repetitive effort during job applications while keeping the candidate involved in the final decision-making process.

## Project Overview

The Job Assistant Bot searches for job opportunities on LinkedIn based on the candidate's configured skills, preferred job roles, locations, and experience. It extracts the available job information and retrieves the job description for each opportunity. The job description and candidate information are then analyzed using a Large Language Model running locally through LM Studio and Gemma. The system evaluates the relevance of each job and generates a confidence score to help identify the most suitable opportunities.

## AI-Based Job Matching

The system evaluates job suitability using four main factors: role match, skill match, experience match, and job-description match. Role matching contributes 25% to the final score, skill matching contributes 50%, experience matching contributes 15%, and job-description matching contributes 10%. The final confidence score is calculated by the Python application using these weighted values. Jobs are then sorted according to their confidence scores, allowing the candidate to focus on the most relevant opportunities.

## LLM Integration

The project uses LM Studio to run the Gemma Large Language Model locally. The Python application communicates with the locally running model through an HTTP API using the Python Requests library. The LLM is used for analyzing job descriptions, evaluating candidate-job compatibility, customizing resumes, and generating personalized cover letters. The application sends structured prompts containing the candidate information and job details to the model and processes the returned responses.

## Resume Customization

For jobs that meet the configured confidence threshold, the system generates a customized resume based on the candidate's existing resume and the selected job description. The LLM is instructed to use only information available in the original resume and not invent skills, experience, companies, dates, projects, certifications, or achievements. The generated information is structured into sections such as professional summary, technical skills, training, professional experience, relevant projects, certifications, education, and career objective. The Python application then creates the customized resume as a Word document using the Python-docx library.

## Cover Letter Generation

The system also generates a personalized cover letter for the selected job. The job title, company information, job description, and candidate resume are provided to the LLM. The model generates a structured cover letter while following the candidate's actual experience and skills without inventing information. The generated content is then converted into a formatted Word document.

## Google Sheets Integration

The Job Assistant Bot sends the evaluated job information to a configured Google Sheets endpoint using an HTTP POST request. The stored information can include the job title, company, job link, confidence score, comments, and job description. This provides a centralized way to review and track the jobs identified by the system.

## Human-in-the-Loop

Human approval is an important part of the Job Assistant Bot workflow. The system does not independently decide whether an application should be sent. After generating the customized resume and cover letter, the candidate is shown the job information, confidence score, and generated documents. The candidate can review the opportunity and decide whether to proceed. The email is sent only when the candidate explicitly approves the application by entering "YES". This approach keeps the candidate in control while allowing AI to handle repetitive tasks.

## Email Sending

After human approval, the system can prepare and send an application email using Gmail SMTP and Python's smtplib library. The customized resume and cover letter are attached to the email. Email credentials are handled through environment variables rather than being hard-coded into the application. The email-sending functionality is therefore separated from the main workflow and is triggered only after user approval.

## Project Structure

The project is organized into separate Python modules. `app.py` acts as the main controller and coordinates the complete workflow. `scraper.py` is responsible for searching LinkedIn, extracting job information, and retrieving job descriptions. `resume_generator.py` handles AI-based resume customization and Word document generation. `cover_letter_generator.py` generates personalized cover letters and creates Word documents. `email_sender.py` handles the final email preparation and sending process. `requirements.txt` contains the required Python dependencies, while `config.example.txt` provides a safe example of the configuration format.

## Technologies Used

The project is developed using Python and uses Requests for HTTP communication, BeautifulSoup for HTML parsing and web scraping, Python-docx for Word document generation, LM Studio for local LLM serving, Gemma for AI-based analysis and content generation, Google Sheets integration for storing job results, and Gmail SMTP for sending application emails.

## Configuration

The application uses a local `config.txt` file to store candidate and job-search preferences such as base skill, candidate skill description, target roles, locations, experience, confidence threshold, Google Sheet URL, candidate email, and email-sending settings. The actual `config.txt` file is kept locally and is not uploaded to the repository. A safe `config.example.txt` file is provided in the repository to demonstrate the required configuration format without exposing personal information or credentials.

## Installation and Usage

To run the project, Python and the required dependencies must be installed using the `requirements.txt` file. LM Studio must be installed and configured with the required Gemma model, and the local LM Studio server must be running so that the Python application can communicate with the model. After creating the local `config.txt` file using `config.example.txt` as a reference, the application can be started using `python app.py`. The system then searches for jobs, extracts job descriptions, evaluates them using the LLM, calculates confidence scores, updates the configured Google Sheet, generates documents for suitable opportunities, and waits for human approval before sending an application email.

## Security and Privacy

Sensitive information should not be uploaded to the GitHub repository. This includes the actual `config.txt`, email passwords, Gmail App Passwords, API keys, Google credentials, personal resumes containing private information, and generated application documents containing personal information. The repository uses `.gitignore` to help prevent sensitive files and generated files from being committed accidentally.

## Current Status

Job Assistant Bot is currently a working prototype under development. The core workflow includes job searching, job-description extraction, AI-based job evaluation, confidence scoring, Google Sheets integration, customized resume generation, personalized cover-letter generation, human approval, and optional email sending.

## Future Scope

The project can be further improved by supporting additional job platforms, improving job-description extraction and duplicate detection, introducing more advanced semantic job matching, adding a web-based interface, maintaining application history, providing job application tracking, supporting multiple LLM providers, managing different resume versions, and adding AI-powered interview preparation.

## Project Objective

The objective of Job Assistant Bot is to explore the practical use of Artificial Intelligence in the job-search and application process. The project demonstrates the use of information extraction, natural language understanding, job requirement matching, Large Language Models, content generation, document automation, workflow automation, and human-in-the-loop AI.

## Author

Meenalochani Murukadas

## Key Idea

AI handles the repetitive work, while the candidate remains in control of the final decision.

