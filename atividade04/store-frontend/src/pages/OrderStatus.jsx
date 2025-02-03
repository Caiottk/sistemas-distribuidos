import React, { useState, useEffect } from 'react';

const OrderStatus = () => {
    const [orderStatus, setOrderStatus] = useState([]);

    useEffect(() => {
        // Conecta ao endpoint SSE
        const eventSource = new EventSource('http://localhost:8001/notificacoes');

        // Escuta por mensagens
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setOrderStatus((prevStatus) => [...prevStatus, data]);
        };

        // Fecha a conexão ao desmontar o componente
        return () => {
            eventSource.close();
        };
    }, []);

    return (
        <div className="order-status">
            <h2>Status do Pedido</h2>
            <ul>
                {orderStatus.map((status, index) => (
                    <li key={index}>
                        <strong>Pedido #{status.order_id}</strong>: {status.status}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default OrderStatus;