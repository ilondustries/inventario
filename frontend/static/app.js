class AlmacenApp {
    constructor() {
        this.apiUrl = '/api';
        this.productos = [];
        this.filtroActual = '';
        this.currentUser = null;
        this.init();
    }
    
    async init() {
        // Verificar autenticación primero
        await this.checkAuth();
        if (!this.currentUser) {
            window.location.href = '/login';
            return;
        }
        
        this.loadProductos();
        this.loadEstadisticas();
        this.setupEventListeners();
        this.setupSearchDebounce();
        this.updateUserInfo();
    }
    
    async checkAuth() {
        try {
            const response = await fetch(`${this.apiUrl}/auth/check`);
            const data = await response.json();
            
            if (data.autenticado) {
                this.currentUser = data.usuario;
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Error verificando autenticación:', error);
            return false;
        }
    }
    
    updateUserInfo() {
        if (this.currentUser) {
            const userInfo = document.getElementById('userInfo');
            if (userInfo) {
                userInfo.innerHTML = `
                    <span class="user-name">👤 ${this.currentUser.nombre_completo}</span>
                    <span class="user-role">${this.getRoleDisplay(this.currentUser.rol)}</span>
                    <button onclick="app.logout()" class="btn-logout">🚪 Cerrar Sesión</button>
                `;
            }
        }
    }
    
    getRoleDisplay(rol) {
        const roles = {
            'admin': '👑 Administrador',
            'supervisor': '👨‍💼 Supervisor',
            'operador': '👷 Operador'
        };
        return roles[rol] || rol;
    }
    
    async logout() {
        // Confirmar antes de cerrar sesión
        if (!confirm('¿Estás seguro de que quieres cerrar sesión?')) {
            return;
        }
        
        try {
            this.showNotification('Cerrando sesión...', 'info');
            
            const response = await fetch(`${this.apiUrl}/auth/logout`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Sesión cerrada exitosamente', 'success');
                // Pequeña pausa para mostrar el mensaje
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1000);
            } else {
                throw new Error('Error al cerrar sesión');
            }
        } catch (error) {
            console.error('Error en logout:', error);
            this.showNotification('Error al cerrar sesión', 'error');
            // Redirigir de todas formas después de un momento
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    }
    
    setupEventListeners() {
        // Formulario de productos
        document.getElementById('productoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.guardarProducto();
        });
        
        // Búsqueda
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filtroActual = e.target.value;
            this.filtrarProductos();
        });
        
        // Modal de confirmación
        document.getElementById('confirmYes').addEventListener('click', () => {
            this.confirmarEliminacion();
        });
        
        // Detectar cierre de navegador o pestaña
        window.addEventListener('beforeunload', (e) => {
            this.handleBrowserClose();
        });
        
        // Detectar cuando la página pierde el foco (opcional)
        window.addEventListener('blur', () => {
            this.handlePageBlur();
        });
        
        // Detectar cuando la página recupera el foco
        window.addEventListener('focus', () => {
            this.handlePageFocus();
        });
    }
    
    setupSearchDebounce() {
        let timeout;
        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.buscarProductos();
            }, 300);
        });
    }
    
    async loadProductos() {
        try {
            const response = await fetch(`${this.apiUrl}/productos`);
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            
            const data = await response.json();
            this.productos = data.productos;
            this.renderProductos(this.productos);
        } catch (error) {
            console.error('Error cargando productos:', error);
            this.showNotification('Error al cargar productos', 'error');
        }
    }
    
    async loadEstadisticas() {
        try {
            const response = await fetch(`${this.apiUrl}/estadisticas`);
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            
            const data = await response.json();
            this.updateEstadisticas(data);
        } catch (error) {
            console.error('Error cargando estadísticas:', error);
        }
    }
    
    updateEstadisticas(stats) {
        document.getElementById('totalProductos').textContent = stats.total_productos;
        document.getElementById('stockBajo').textContent = stats.stock_bajo;
        document.getElementById('valorTotal').textContent = `$${stats.valor_total.toFixed(2)}`;
        
        // Resaltar stock bajo
        const stockBajoElement = document.getElementById('stockBajo');
        if (stats.stock_bajo > 0) {
            stockBajoElement.classList.add('warning');
        } else {
            stockBajoElement.classList.remove('warning');
        }
    }
    
    async guardarProducto() {
        const productoId = document.getElementById('productoId').value;
        const formData = {
            codigo_barras: document.getElementById('codigoBarras').value,
            nombre: document.getElementById('nombre').value,
            descripcion: document.getElementById('descripcion').value,
            cantidad: parseInt(document.getElementById('cantidad').value) || 0,
            cantidad_minima: parseInt(document.getElementById('cantidadMinima').value) || 0,
            ubicacion: document.getElementById('ubicacion').value,
            categoria: document.getElementById('categoria').value,
            precio_unitario: parseFloat(document.getElementById('precioUnitario').value) || 0
        };
        
        try {
            const url = productoId ? 
                `${this.apiUrl}/productos/${productoId}` : 
                `${this.apiUrl}/productos`;
            
            const method = productoId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error en la operación');
            }
            
            const result = await response.json();
            this.showNotification(result.mensaje, 'success');
            this.limpiarFormulario();
            this.loadProductos();
            this.loadEstadisticas();
        } catch (error) {
            console.error('Error:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    editarProducto(productoId) {
        const producto = this.productos.find(p => p.id === productoId);
        if (!producto) return;
        
        // Llenar formulario
        document.getElementById('productoId').value = producto.id;
        document.getElementById('codigoBarras').value = producto.codigo_barras || '';
        document.getElementById('nombre').value = producto.nombre;
        document.getElementById('descripcion').value = producto.descripcion || '';
        document.getElementById('cantidad').value = producto.cantidad;
        document.getElementById('cantidadMinima').value = producto.cantidad_minima || '';
        document.getElementById('ubicacion').value = producto.ubicacion || '';
        document.getElementById('categoria').value = producto.categoria || '';
        document.getElementById('precioUnitario').value = producto.precio_unitario || '';
        
        // Cambiar título y botones
        document.getElementById('formTitle').textContent = '✏️ Editar Producto';
        document.getElementById('submitBtn').textContent = 'Actualizar Producto';
        document.getElementById('cancelBtn').style.display = 'block';
        
        // Scroll al formulario
        document.querySelector('.form-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    cancelarEdicion() {
        this.limpiarFormulario();
        document.getElementById('formTitle').textContent = '➕ Agregar Producto';
        document.getElementById('submitBtn').textContent = 'Guardar Producto';
        document.getElementById('cancelBtn').style.display = 'none';
    }
    
    limpiarFormulario() {
        document.getElementById('productoForm').reset();
        document.getElementById('productoId').value = '';
        this.cancelarEdicion();
    }
    
    async eliminarProducto(productoId) {
        const producto = this.productos.find(p => p.id === productoId);
        if (!producto) return;
        
        this.mostrarModal(
            `¿Estás seguro de que quieres eliminar "${producto.nombre}"?`,
            productoId
        );
    }
    
    mostrarModal(mensaje, productoId) {
        document.getElementById('confirmMessage').textContent = mensaje;
        document.getElementById('confirmModal').style.display = 'block';
        document.getElementById('confirmYes').onclick = () => this.confirmarEliminacion(productoId);
    }
    
    cerrarModal() {
        document.getElementById('confirmModal').style.display = 'none';
    }
    
    async confirmarEliminacion(productoId) {
        try {
            const response = await fetch(`${this.apiUrl}/productos/${productoId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al eliminar');
            }
            
            const result = await response.json();
            this.showNotification(result.mensaje, 'success');
            this.cerrarModal();
            this.loadProductos();
            this.loadEstadisticas();
        } catch (error) {
            console.error('Error:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    buscarProductos() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        this.filtroActual = searchTerm;
        this.filtrarProductos();
    }
    
    filtrarProductos() {
        const productosFiltrados = this.productos.filter(producto => {
            if (!this.filtroActual) return true;
            
            return producto.nombre.toLowerCase().includes(this.filtroActual) ||
                   (producto.codigo_barras && producto.codigo_barras.toLowerCase().includes(this.filtroActual)) ||
                   (producto.ubicacion && producto.ubicacion.toLowerCase().includes(this.filtroActual)) ||
                   (producto.categoria && producto.categoria.toLowerCase().includes(this.filtroActual));
        });
        
        this.renderProductos(productosFiltrados);
    }
    
    renderProductos(productos) {
        const container = document.getElementById('productosList');
        container.innerHTML = '';
        
        if (productos.length === 0) {
            container.innerHTML = `
                <div class="no-products">
                    <p>No se encontraron productos</p>
                </div>
            `;
            return;
        }
        
        productos.forEach(producto => {
            const card = document.createElement('div');
            card.className = 'producto-card';
            
            // Agregar clase para stock bajo
            if (producto.cantidad_minima > 0 && producto.cantidad <= producto.cantidad_minima) {
                card.classList.add('stock-bajo');
            }
            
            const cantidadClass = producto.cantidad <= 5 ? 'cantidad-baja' : '';
            const precio = producto.precio_unitario ? `$${producto.precio_unitario.toFixed(2)}` : 'N/A';
            
            card.innerHTML = `
                <div class="producto-info">
                    <h3>${producto.nombre}</h3>
                    ${producto.descripcion ? `<p class="descripcion">${producto.descripcion}</p>` : ''}
                    <div class="producto-stats">
                        <span>📦 Cantidad: <span class="${cantidadClass}">${producto.cantidad}</span></span>
                        ${producto.ubicacion ? `<span>📍 ${producto.ubicacion}</span>` : ''}
                        ${producto.categoria ? `<span>🏷️ ${producto.categoria}</span>` : ''}
                        <span>💰 ${precio}</span>
                    </div>
                </div>
                <div class="producto-actions">
                    <button onclick="app.editarProducto(${producto.id})" class="btn-edit" title="Editar">✏️</button>
                    <button onclick="app.eliminarProducto(${producto.id})" class="btn-delete" title="Eliminar">🗑️</button>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    handleBrowserClose() {
        // Enviar señal de logout al cerrar navegador
        if (navigator.sendBeacon) {
            navigator.sendBeacon(`${this.apiUrl}/auth/logout`);
        } else {
            // Fallback para navegadores que no soportan sendBeacon
            fetch(`${this.apiUrl}/auth/logout`, {
                method: 'POST',
                keepalive: true
            }).catch(() => {
                // Ignorar errores al cerrar
            });
        }
    }
    
    handlePageBlur() {
        // Opcional: Marcar que la página perdió el foco
        this.pageBlurred = true;
    }
    
    handlePageFocus() {
        // Opcional: Verificar sesión cuando la página recupera el foco
        if (this.pageBlurred) {
            this.pageBlurred = false;
            this.checkSessionValidity();
        }
    }
    
    async checkSessionValidity() {
        try {
            const response = await fetch(`${this.apiUrl}/auth/check`);
            const data = await response.json();
            
            if (!data.autenticado) {
                this.showNotification('Sesión expirada. Redirigiendo al login...', 'warning');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            }
        } catch (error) {
            console.log('Error verificando sesión:', error);
        }
    }
}

// Inicializar la aplicación cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AlmacenApp();
});

// Cerrar modal al hacer clic fuera
window.addEventListener('click', (event) => {
    const modal = document.getElementById('confirmModal');
    if (event.target === modal) {
        app.cerrarModal();
    }
}); 