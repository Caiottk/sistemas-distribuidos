import { useEffect, useState } from "react";

function ProductList({ addToCart }) {
  const [products, setProducts] = useState([]);

  // Function to fetch initial product list
  const fetchProducts = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/products");
      const data = await res.json();
      setProducts(data.products);
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  };

  useEffect(() => {
    fetchProducts(); // Fetch initial product list

    // Set up SSE connection
    const eventSource = new EventSource("http://127.0.0.1:8000/stream-products");

    eventSource.onmessage = (event) => {
      const updatedProducts = JSON.parse(event.data);
      setProducts(updatedProducts.products);
    };

    eventSource.onerror = () => {
      console.error("SSE connection failed");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Products</h1>
      <div className="grid grid-cols-3 gap-4">
        {products.map((product) => (
          <div key={product.id} className="p-4 border rounded">
            <h2>{product.name}</h2>
            <p>${product.price}</p>
            <button onClick={() => addToCart(product)} className="bg-blue-500 text-white px-3 py-1 mt-2">
              Add to Cart
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProductList;
