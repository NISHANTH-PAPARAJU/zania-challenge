import React, { useState } from 'react';
import axios from 'axios';
import './App.css';


function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [filename, setFilename] = useState('');
  const [question, setQuestion] = useState('');
  const [instruction, setInstruction] = useState('');
  const [response, setResponse] = useState(null);

  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  });

  // Handle file selection
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Upload file to backend
  const handleUpload = async () => {
    if (selectedFile) {
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const res = await api.post('/uploadfile', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        setFilename(res.data.file_path); 
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
  };

  // Handle question submit
  const handleSubmit = async () => {
    if (filename && question && instruction) {
      try {
        const res = await api.post('/api/v1/doc-qa', {
          "file_location": filename,
          "user_query": question + "\n" + instruction,
        });
        setResponse("Message: " + res.data.message + "\n request_id: " + res.data.request_id); // Assuming backend returns answer in `answer` field
      } catch (error) {
        console.error('Error getting answer:', error);
      }
    }
  };

  return (
    <div className="App">
      <h1>Document Q&A Application</h1>

      <div>
        <input
          type="file"
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
          disabled={!!filename}
        />
        <button onClick={handleUpload} disabled={!selectedFile || !!filename}>
          Upload File
        </button>
      </div>

      <div>
        <p>Questions: </p>
        <textarea
          placeholder="Ask your question here..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows="4"
          cols="50"
        />
      </div>

      <div>
        <p>instructions: </p>
        <textarea
          placeholder="Put your instructions here"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          rows="4"
          cols="50"
        />
      </div>

      <button onClick={handleSubmit} disabled={!filename || !question || !instruction }>
        Submit Question
      </button>

      {response && (
        <div>
          <h3>Answer:</h3>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}

export default App;
