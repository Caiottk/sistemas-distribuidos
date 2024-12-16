import { createContext, useEffect, useState } from 'react';
import { products } from '../assets/assets';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

export const ShopContext = createContext();

const ShopContextProvider = (props) => {
  const currency = 'R$';
  const delivery_fee = 10;
  const [search, setSearch] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [orders, setOrders] = useState([]); // New state to hold orders
  const navigate = useNavigate();

  useEffect(() => {
    // Any side effects related to navigation can be handled here
  }, [navigate]);

  const addToCart = async(itemId, size) => {

    if (!size) {
      toast.error('Please select a size');
      return;
    }

    let cartData = structuredClone(cartItems);
    if(cartData[itemId]){
      if(cartData[itemId][size]){
        cartData[itemId][size] += 1;
      }
      else{
        cartData[itemId][size] = 1;
      }
    }
    else{
      cartData[itemId] = {};
      cartData[itemId][size] = 1;
    }
    setCartItems(cartData);
  }

  const getCartCount = () => {
    let count = 0;
    for (const item in cartItems) {
      for (const size in cartItems[item]) {
        try {
          if(cartItems[item][size] > 0){
            count += cartItems[item][size];
          }
        } catch (error) {
          console.log(error);
        }
      }
    }
    return count;
  }

  const updateQuantity = async(itemId, size, quantity) => {
    let cartData = structuredClone(cartItems);
    cartData[itemId][size] = quantity;
    setCartItems(cartData);
  }

  const getCartAmount = () => {
    let amount = 0;
    for (const item in cartItems) {
      let itemInfo = products.find(product => product._id === item);
      for (const size in cartItems[item]) {
        try {
          if(cartItems[item][size] > 0){
            amount += itemInfo.price * cartItems[item][size];
          }
        } catch (error) {
          console.log(error);
        }
      }
    }
    return amount;
  }

  const addOrder = () => {
    let tempOrders = structuredClone(orders);
    let newOrder = [];

    for (const item in cartItems) {
      for (const size in cartItems[item]) {
        if (cartItems[item][size] > 0) {
          newOrder.push({
            _id: item,
            size,
            quantity: cartItems[item][size],
          });
        }
      }
    }
    setOrders([...tempOrders, ...newOrder]);
    //setCartItems({}); // Clear cart after placing the order
  };

  const value = {
    products, currency, delivery_fee,
    search, setSearch, showSearch, setShowSearch,
    cartItems, setCartItems, addToCart,
    getCartCount, updateQuantity, getCartAmount,
    navigate, addOrder
  }

  return (
      <ShopContext.Provider value={value}>
        {props.children}
      </ShopContext.Provider>
  )
}

export default ShopContextProvider;