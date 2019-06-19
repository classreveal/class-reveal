import React, { Component } from 'react';
import './App.css';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      data: {}
    };
  }

  componentDidMount() {
    fetch("http://127.0.0.1/api").then(
      response => response.json()
    ).then(
      json => {
        this.setState({ data: json });
      }
    );
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>
            {this.state.data.message}
          </p>
        </header>
      </div>
    );
  }
}

export default App;
