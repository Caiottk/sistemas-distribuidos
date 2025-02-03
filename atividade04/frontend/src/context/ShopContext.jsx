import { createContext, useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export const ShopContext = createContext();

const ShopContextProvider = (props) => {
  const currency = 'R$';
  const delivery_fee = 10;
  const [search, setSearch] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [orders, setOrders] = useState([]); // Estado para armazenar pedidos
  const [notifications, setNotifications] = useState([]); // Estado para notificações
  const navigate = useNavigate();

  // Efeito para conectar ao SSE e receber notificações
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:5002/notificacoes');

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setNotifications((prev) => [...prev, data]);
      toast.info(`Pedido ${data.pedido_id}: ${data.status}`); // Exibir notificação como toast
    };

    eventSource.onerror = (error) => {
      console.error('Erro na conexão SSE:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Buscar produtos do backend
  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:5000/produtos');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar produtos:', error);
      toast.error('Erro ao carregar produtos');
      return [];
    }
  };

  // Adicionar item ao carrinho
  const addToCart = async (itemId, size) => {
    if (!size) {
      toast.error('Selecione um tamanho');
      return;
    }
  
    try {
      // Verificar disponibilidade no microsserviço de Estoque
      const response = await axios.get(`http://localhost:5003/estoque/produtos/${itemId}/disponibilidade?size=${size}`);
      const { available, quantity } = response.data;
  
      if (!available) {
        toast.error('Produto indisponível no tamanho selecionado');
        return;
      }
  
      // Adicionar ao carrinho
      let cartData = structuredClone(cartItems);
      if (cartData[itemId]) {
        if (cartData[itemId][size]) {
          cartData[itemId][size] += 1;
        } else {
          cartData[itemId][size] = 1;
        }
      } else {
        cartData[itemId] = {};
        cartData[itemId][size] = 1;
      }
  
      setCartItems(cartData);
      toast.success('Item adicionado ao carrinho');
    } catch (error) {
      console.error('Erro ao verificar disponibilidade:', error);
      toast.error('Erro ao verificar disponibilidade');
    }
  };

  // Atualizar quantidade de um item no carrinho
  const updateQuantity = async (itemId, size, quantity) => {
    let cartData = structuredClone(cartItems);
    cartData[itemId][size] = quantity;
    setCartItems(cartData);
  };

  // Calcular o total de itens no carrinho
  const getCartCount = () => {
    let count = 0;
    for (const item in cartItems) {
      for (const size in cartItems[item]) {
        try {
          if (cartItems[item][size] > 0) {
            count += cartItems[item][size];
          }
        } catch (error) {
          console.log(error);
        }
      }
    }
    return count;
  };

  // Calcular o valor total do carrinho
  const getCartAmount = async () => {
    let amount = 0;
    const products = await fetchProducts(); // Buscar produtos do backend

    for (const item in cartItems) {
      const itemInfo = products.find((product) => product._id === item);
      for (const size in cartItems[item]) {
        try {
          if (cartItems[item][size] > 0) {
            amount += itemInfo.price * cartItems[item][size];
          }
        } catch (error) {
          console.log(error);
        }
      }
    }
    return amount;
  };

  // Criar um novo pedido
  const addOrder = async () => {
    const orderDetails = {
      items: cartItems,
      total: await getCartAmount(),
    };

    try {
      const response = await axios.post('http://localhost:5000/pedidos', orderDetails);
      setOrders((prevOrders) => [...prevOrders, response.data]);
      setCartItems({}); // Limpar o carrinho após criar o pedido
      toast.success('Pedido criado com sucesso!');
      navigate('/orders'); // Redirecionar para a página de pedidos
    } catch (error) {
      console.error('Erro ao criar pedido:', error);
      toast.error('Erro ao criar pedido');
    }
  };

  // Valor do contexto
  const value = {
    currency,
    delivery_fee,
    search,
    setSearch,
    showSearch,
    setShowSearch,
    cartItems,
    setCartItems,
    addToCart,
    getCartCount,
    updateQuantity,
    getCartAmount,
    addOrder,
    orders,
    notifications,
    fetchProducts,
  };

  return (
    <ShopContext.Provider value={value}>
      {props.children}
    </ShopContext.Provider>
  );
};

export default ShopContextProvider;