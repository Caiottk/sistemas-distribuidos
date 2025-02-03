import { Link } from "react-router-dom";

function Cart({ cart, removeFromCart, updateQuantity }) {
  return (
    <div className="w-1/4 p-4 border-r">
      <h2 className="text-lg font-bold">Cart</h2>
      {cart.length === 0 && <p>No items in cart.</p>}
      {cart.map((item) => (
        <div key={item.id} className="p-2 border-b">
          <p>{item.name} (${item.price})</p>
          <div className="flex items-center">
            <button onClick={() => updateQuantity(item.id, -1)}>-</button>
            <span className="mx-2">{item.quantity}</span>
            <button onClick={() => updateQuantity(item.id, 1)}>+</button>
          </div>
          <button onClick={() => removeFromCart(item.id)} className="text-red-500">
            Remove
          </button>
        </div>
      ))}
      {cart.length > 0 && (
        <Link to="/checkout" className="block bg-green-500 text-white p-2 mt-4 text-center">
          Checkout
        </Link>
      )}
    </div>
  );
}

export default Cart;
