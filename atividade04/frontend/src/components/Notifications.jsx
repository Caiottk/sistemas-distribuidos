import React, { useEffect, useState } from 'react';

const Notifications = () => {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:5173/notifications');

    eventSource.onmessage = (event) => {
      const newMessage = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    };

    eventSource.onerror = () => {
      console.error('EventSource failed. Reconnecting...');
      eventSource.close();
      setTimeout(() => {
        eventSource = new EventSource('http://localhost:5173/notifications');
      }, 3000);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div>
      <h2>Notifications</h2>
      <ul>
        {messages.map((message, index) => (
          <li key={index}>{message}</li>
        ))}
      </ul>
    </div>
  );
};

export default Notifications;