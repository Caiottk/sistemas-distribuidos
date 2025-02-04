import React, { useState, useEffect } from 'react';

const OrderStatus = () => {
    const [orders, setOrders] = useState([]);

    // Listen for real-time updates using SSE
    useEffect(() => {
        const eventSource = new EventSource('http://localhost:8001/notificacao');

        eventSource.onmessage = (event) => {
            const order = JSON.parse(event.data); // Parse the incoming order

            // Update or add the order in the state
            setOrders((prevOrders) => {
                const orderIndex = prevOrders.findIndex(
                    (o) => o.order_id === order.order_id
                );

                if (orderIndex !== -1) {
                    // If the order exists, update it
                    const newOrders = [...prevOrders];
                    newOrders[orderIndex] = order;
                    return newOrders;
                } else {
                    // If the order doesn't exist, add it to the list
                    return [...prevOrders, order];
                }
            });
        };

        // Cleanup on component unmount
        return () => {
            eventSource.close();
        };
    }, []);

    return (
        <div className="order-status">
            <h2>Status do Pedido</h2>
            <ul>
                {orders.map((order) => (
                    <li key={order.order_id}>
                        <strong>Pedido #{order.order_id}</strong>: {order.status}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default OrderStatus;