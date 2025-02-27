<script>
    let username = "";
    let password = "";
  
    async function login() {
      const response = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
  
      const data = await response.json();
      alert(data.message);
    }
  </script>
  
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="w-full max-w-md bg-white p-6 rounded-lg shadow-md">
      <h1 class="text-2xl font-bold text-center text-gray-700 mb-6">Login</h1>
      
      <div class="mb-4">
        <label for="username" class="block text-gray-600 text-sm mb-1">Username</label>
        <input id="username" type="text" bind:value={username} class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-400" placeholder="Enter your username">
      </div>
  
      <div class="mb-4">
        <label for="password" class="block text-gray-600 text-sm mb-1">Password</label>
        <input id="password" type="password" bind:value={password} class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-400" placeholder="Enter your password">
      </div>
  
      <button on:click={login} class="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600">
        Login
      </button>
  
      <p class="text-center text-sm text-gray-500 mt-4">
        Don't have an account? <a href="/register" class="text-blue-500 hover:underline">Register here</a>
      </p>
    </div>
  </div>
  