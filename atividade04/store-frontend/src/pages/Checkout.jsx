import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Checkout({ cart }) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [card, setCard] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleCheckout = async () => {
    if (!name || !address || !card) {
      alert("Please fill out all fields.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          address,
          card,
          cart,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to place order.");
      }

      const data = await response.json();
      console.log("Order placed successfully:", data);

      // Navigate to the order status page
      navigate("/order-status");
    } catch (error) {
      console.error("Error placing order:", error);
      setError("Failed to place order. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-xl font-bold">Checkout</h1>
      <input
        type="text"
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="block border p-2 mb-2"
      />
      <input
        type="text"
        placeholder="Address"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        className="block border p-2 mb-2"
      />
      <input
        type="text"
        placeholder="Credit Card"
        value={card}
        onChange={(e) => setCard(e.target.value)}
        className="block border p-2 mb-2"
      />
      <button
        onClick={handleCheckout}
        disabled={isLoading}
        className="bg-blue-500 text-white p-2"
      >
        {isLoading ? "Placing Order..." : "Confirm Order"}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
}

export default Checkout;