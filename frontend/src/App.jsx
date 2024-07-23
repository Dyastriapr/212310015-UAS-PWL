import React from 'react'
import MainPage from './module/MainPage'
import Navbar from './components/Navbar'
import Foo from './components/Foo'


const App = () => {
  return (
    <div>
      <Navbar />
      <div >
      <MainPage />
      </div>
    <Foo/>
    </div>
    
  )
}

export default App