<script>
    let username = "";
    let password = "";
  
    async function register() {
      const response = await fetch("http://localhost:5000/register", {
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
      <h1 class="text-2xl font-bold text-center text-gray-700 mb-6">Register</h1>
      
      <div class="mb-4">
        <label for="username" class="block text-gray-600 text-sm mb-1">Username</label>
        <input id="username" type="text" bind:value={username} class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-400" placeholder="Choose a username">
      </div>
  
      <div class="mb-4">
        <label for="password" class="block text-gray-600 text-sm mb-1">Password</label>
        <input id="password" type="password" bind:value={password} class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-400" placeholder="Choose a password">
      </div>
  
      <button on:click={register} class="w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600">
        Register
      </button>
  
      <p class="text-center text-sm text-gray-500 mt-4">
        Already have an account? <a href="/login" class="text-blue-500 hover:underline">Login here</a>
      </p>
    </div>
  </div>
  