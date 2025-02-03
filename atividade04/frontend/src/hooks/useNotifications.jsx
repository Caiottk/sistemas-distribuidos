import { useEffect, useState } from 'react';

const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Conectar ao endpoint SSE
    const eventSource = new EventSource('http://localhost:5002/notificacoes');

    // Ouvir eventos
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setNotifications((prev) => [...prev, data]);
    };

    // Lidar com erros
    eventSource.onerror = (error) => {
      console.error('Erro na conexão SSE:', error);
      eventSource.close();
    };

    // Fechar a conexão ao desmontar o componente
    return () => {
      eventSource.close();
    };
  }, []);

  return notifications;
};

export default useNotifications;