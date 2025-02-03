import { Routes, Route } from "react-router-dom";
import ProductList from "./components/ProductList";
import Checkout from "./pages/Checkout";
import OrderStatus from "./pages/OrderStatus";
import Cart from "./components/Cart";
import { useState } from "react";

function App() {
  const [cart, setCart] = useState([]);

  const addToCart = (product) => {
    setCart((prevCart) => {
      const existingItem = prevCart.find((item) => item.id === product.id);
      if (existingItem) {
        return prevCart.map((item) =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prevCart, { ...product, quantity: 1 }];
    });
  };

  const removeFromCart = (productId) => {
    setCart((prevCart) =>
      prevCart.filter((item) => item.id !== productId)
    );
  };

  const updateQuantity = (productId, amount) => {
    setCart((prevCart) =>
      prevCart.map((item) =>
        item.id === productId ? { ...item, quantity: Math.max(item.quantity + amount, 1) } : item
      )
    );
  };

  return (
    <div className="flex">
      <Cart cart={cart} removeFromCart={removeFromCart} updateQuantity={updateQuantity} />
      <div className="p-4 w-full">
        <Routes>
          <Route path="/" element={<ProductList addToCart={addToCart} />} />
          <Route path="/checkout" element={<Checkout cart={cart} />} />
          <Route path="/order-status" element={<OrderStatus />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
