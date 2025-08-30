import octalLogo from './assets/octal.svg'
import './App.css'

function App() {
  return (
    <>
      <div>
        <a href="https://octal.school" target="_blank">
          <img src={octalLogo} className="logo" alt="Octal logo" />
        </a>
      </div>
      <h1>React + Octal</h1>
    </>
  )
}

export default App
