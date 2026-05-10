import { Route, Routes } from 'react-router-dom'
import './App.css'
import { RequireAuth } from './context/AuthContext'
import RootLayout from './layout/RootLayout'
import Budget from './pages/Budget'
import Home from './pages/Home'
import Login from './pages/Login'
import Meals from './pages/Meals'
import NotFound from './pages/NotFound'
import Pantry from './pages/Pantry'
import Planner from './pages/Planner'
import Register from './pages/Register'
import ShoppingList from './pages/ShoppingList'

function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route element={<RequireAuth />}>
          <Route index element={<Home />} />
          <Route path="pantry" element={<Pantry />} />
          <Route path="meals" element={<Meals />} />
          <Route path="shopping-list" element={<ShoppingList />} />
          <Route path="budget" element={<Budget />} />
          <Route path="planner" element={<Planner />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
