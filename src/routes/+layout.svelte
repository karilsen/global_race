<script>
	import "../app.css";
  </script>
  
  <header class="bg-blue-600 text-white py-4 shadow-md">
	<div class="container mx-auto flex justify-between items-center px-6">
	  <h1 class="text-2xl font-bold">🌍 The Global Race</h1>
	  <nav class="space-x-6">
		<a href="/login" class="hover:underline">Login</a>
		<a href="/register" class="hover:underline">Register</a>
		<a href="/map" class="hover:underline">Map</a> 
	  </nav>
	</div>
  </header>
  
  <main class="container mx-auto px-6 mt-8">
	<slot />
  </main>
  