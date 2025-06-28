class AlmacenApp {
    constructor() {
        this.apiUrl = '/api';
        this.productos = [];
        this.filtroActual = '';
        this.currentUser = null;
        this.filtroStockBajo = false;
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
        this.initTickets();
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
            
            // Ocultar formulario de productos para usuarios que no sean administradores
            this.updateFormVisibility();
        }
    }
    
    updateFormVisibility() {
        const formSection = document.querySelector('.form-section');
        const mainContent = document.querySelector('.main-content');
        const adminMenu = document.getElementById('adminMenu');
        
        if (formSection && mainContent) {
            if (this.currentUser && this.currentUser.rol === 'admin') {
                // Administradores: acceso completo con menú de pestañas
                formSection.style.display = 'block';
                mainContent.classList.remove('form-hidden');
                mainContent.classList.add('admin-layout');
                
                // Mostrar menú de administrador
                if (adminMenu) {
                    adminMenu.style.display = 'flex';
                }
                
                // Mostrar la primera sección por defecto
                this.mostrarSeccion('form-section');
            } else if (this.currentUser && (this.currentUser.rol === 'supervisor' || this.currentUser.rol === 'operador')) {
                // Supervisores y operadores: pueden ver inventario y tickets, pero no gestión de herramientas
                formSection.style.display = 'none';
                mainContent.classList.remove('form-hidden');
                mainContent.classList.add('admin-layout');
                
                // Mostrar menú de administrador pero ocultar pestaña de gestión
                if (adminMenu) {
                    adminMenu.style.display = 'flex';
                    
                    // Ocultar pestaña de gestión de herramientas para no-admin
                    const gestionTab = adminMenu.querySelector('[data-section="form-section"]');
                    if (gestionTab) {
                        gestionTab.style.display = 'none';
                    }
                }
                
                // Mostrar sección de productos por defecto
                this.mostrarSeccion('products-section');
            } else {
                // Usuarios sin rol específico: solo inventario
                formSection.style.display = 'none';
                mainContent.classList.add('form-hidden');
                mainContent.classList.remove('admin-layout');
                
                // Ocultar menú de administrador
                if (adminMenu) {
                    adminMenu.style.display = 'none';
                }
                
                // Mostrar sección de productos para usuarios no-admin
                this.mostrarSeccion('products-section');
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
        
        // Búsqueda con soporte de teclas
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {
            this.filtroActual = e.target.value;
            this.filtrarProductos();
        });
        
        // Tecla Escape para limpiar búsqueda
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                searchInput.value = '';
                this.filtroActual = '';
                
                // Si el filtro de stock bajo está activo, también limpiarlo
                if (this.filtroStockBajo) {
                    this.desactivarFiltroStockBajo();
                } else {
                    this.filtrarProductos();
                }
            }
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
                this.filtrarProductos();
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
        document.getElementById('valorTotal').textContent = `$${stats.valor_total.toFixed(2)}`;
        
        // Configurar indicador de stock bajo como clickeable
        const stockBajoElement = document.getElementById('stockBajo');
        const stockBajoContainer = document.getElementById('stockBajoContainer');
        stockBajoElement.textContent = stats.stock_bajo;
        
        if (stats.stock_bajo > 0) {
            stockBajoElement.classList.add('warning');
            stockBajoContainer.classList.add('clickeable');
            stockBajoContainer.title = `Hacer clic para ver ${stats.stock_bajo} producto(s) con stock bajo`;
            stockBajoContainer.onclick = () => this.filtrarStockBajo();
        } else {
            stockBajoElement.classList.remove('warning');
            stockBajoContainer.classList.remove('clickeable', 'filtro-activo');
            stockBajoContainer.title = '';
            stockBajoContainer.onclick = null;
        }
    }
    
    filtrarStockBajo() {
        // Si ya está activo el filtro de stock bajo, desactivarlo
        if (this.filtroStockBajo) {
            this.desactivarFiltroStockBajo();
            return;
        }
        
        // Activar filtro de stock bajo
        this.filtroStockBajo = true;
        
        // Filtrar productos con stock bajo
        const productosStockBajo = this.productos.filter(producto => {
            return producto.cantidad_minima > 0 && producto.cantidad <= producto.cantidad_minima;
        });
        
        // Actualizar indicador visual
        const stockBajoContainer = document.getElementById('stockBajoContainer');
        stockBajoContainer.classList.add('filtro-activo');
        stockBajoContainer.title = 'Hacer clic para quitar filtro de stock bajo';
        
        // Mostrar productos filtrados
        this.renderProductos(productosStockBajo);
        
        // Mostrar notificación
        this.showNotification(`Mostrando ${productosStockBajo.length} producto(s) con stock bajo`, 'warning');
    }
    
    desactivarFiltroStockBajo() {
        this.filtroStockBajo = false;
        
        // Restaurar indicador visual
        const stockBajoContainer = document.getElementById('stockBajoContainer');
        stockBajoContainer.classList.remove('filtro-activo');
        stockBajoContainer.title = 'Hacer clic para ver productos con stock bajo';
        
        // Mostrar todos los productos
        this.filtrarProductos();
        
        // Mostrar notificación
        this.showNotification('Filtro de stock bajo desactivado', 'info');
    }
    
    async guardarProducto() {
        const productoId = document.getElementById('productoId').value;
        const formData = {
            nombre: document.getElementById('nombre').value,
            descripcion: document.getElementById('descripcion').value,
            cantidad: parseInt(document.getElementById('cantidad').value) || 0,
            cantidad_minima: parseInt(document.getElementById('cantidadMinima').value) || 0,
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
        document.getElementById('nombre').value = producto.nombre;
        document.getElementById('descripcion').value = producto.descripcion || '';
        document.getElementById('cantidad').value = producto.cantidad;
        document.getElementById('cantidadMinima').value = producto.cantidad_minima || '';
        document.getElementById('categoria').value = producto.categoria || '';
        document.getElementById('precioUnitario').value = producto.precio_unitario || '';
        
        // Cambiar título y botones
        document.getElementById('formTitle').textContent = '✏️ Editar Herramienta';
        document.getElementById('submitBtn').textContent = 'Actualizar Herramienta';
        document.getElementById('cancelBtn').style.display = 'block';
        
        // Scroll al formulario
        document.querySelector('.form-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    cancelarEdicion() {
        this.limpiarFormulario();
        document.getElementById('formTitle').textContent = '➕ Agregar Herramienta';
        document.getElementById('submitBtn').textContent = 'Guardar Herramienta';
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
            `¿Estás seguro de que quieres eliminar la herramienta "${producto.nombre}"?`,
            productoId
        );
    }
    
    mostrarModal(mensaje, productoId) {
        document.getElementById('confirmMessage').textContent = mensaje;
        document.getElementById('confirmModal').style.display = 'block';
        document.getElementById('confirmYes').onclick = () => this.confirmarEliminacion(productoId);
        // Prevenir scroll del body
        document.body.classList.add('modal-open');
    }
    
    cerrarModal() {
        document.getElementById('confirmModal').style.display = 'none';
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
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
    
    filtrarProductos() {
        let productosFiltrados = this.productos;
        
        // Aplicar filtro de stock bajo si está activo
        if (this.filtroStockBajo) {
            productosFiltrados = productosFiltrados.filter(producto => {
                return producto.cantidad_minima > 0 && producto.cantidad <= producto.cantidad_minima;
            });
        }
        
        // Aplicar filtro de búsqueda si hay término de búsqueda
        if (this.filtroActual && this.filtroActual.trim() !== '') {
            productosFiltrados = productosFiltrados.filter(producto => {
                return producto.nombre.toLowerCase().includes(this.filtroActual) ||
                       (producto.codigo_barras && producto.codigo_barras.toLowerCase().includes(this.filtroActual)) ||
                       (producto.ubicacion && producto.ubicacion.toLowerCase().includes(this.filtroActual)) ||
                       (producto.categoria && producto.categoria.toLowerCase().includes(this.filtroActual));
            });
        }
        
        this.renderProductos(productosFiltrados);
    }
    
    renderProductos(productos) {
        const container = document.getElementById('productosList');
        container.innerHTML = '';
        
        if (productos.length === 0) {
            container.innerHTML = `
                <div class="no-products">
                    <p>No se encontraron herramientas</p>
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
            
            // Determinar qué botones mostrar según el rol
            const isAdmin = this.currentUser && this.currentUser.rol === 'admin';
            const actionButtons = isAdmin ? `
                <button onclick="app.editarProducto(${producto.id})" class="btn-edit" title="Editar">✏️</button>
                <button onclick="app.eliminarProducto(${producto.id})" class="btn-delete" title="Eliminar">🗑️</button>
            ` : '';
            
            // Solo mostrar botón QR para administradores
            const qrButton = isAdmin ? `
                <button onclick="app.mostrarQrProducto(${producto.id})" class="btn-qr" title="Ver QR">🔳 QR</button>
            ` : '';
            
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
                    ${actionButtons}
                    ${qrButton}
                </div>
            `;
            
            container.appendChild(card);
        });
        
        // Agregar mensaje de resultados de búsqueda al final
        this.agregarMensajeResultados(productos);
    }
    
    agregarMensajeResultados(productos) {
        const container = document.getElementById('productosList');
        const totalProductos = this.productos.length;
        const productosMostrados = productos.length;
        
        // Crear elemento para el mensaje de resultados
        const mensajeElement = document.createElement('div');
        mensajeElement.className = 'search-results-message';
        
        // Determinar qué mensaje mostrar
        let mensajeHTML = '';
        
        if (this.filtroStockBajo && this.filtroActual && this.filtroActual.trim() !== '') {
            // Ambos filtros activos
            mensajeHTML = `
                <p>🔍 Se encontraron <strong>${productosMostrados}</strong> de <strong>${totalProductos}</strong> herramientas con stock bajo que coinciden con "<strong>${this.filtroActual}</strong>"</p>
                <p>⚠️ Filtro de stock bajo activo</p>
            `;
        } else if (this.filtroStockBajo) {
            // Solo filtro de stock bajo activo
            mensajeHTML = `
                <p>⚠️ Mostrando <strong>${productosMostrados}</strong> de <strong>${totalProductos}</strong> herramientas con stock bajo</p>
                <p>💡 Hacer clic en "Stock Bajo" en la barra superior para quitar el filtro</p>
            `;
        } else if (this.filtroActual && this.filtroActual.trim() !== '') {
            // Solo búsqueda activa
            if (productosMostrados === 0) {
                mensajeHTML = `
                    <p>🔍 No se encontraron herramientas que coincidan con "<strong>${this.filtroActual}</strong>"</p>
                    <p>Total de herramientas en inventario: <strong>${totalProductos}</strong></p>
                `;
            } else if (productosMostrados === totalProductos) {
                mensajeHTML = `
                    <p>🔍 Mostrando todas las <strong>${productosMostrados}</strong> herramientas</p>
                `;
            } else {
                mensajeHTML = `
                    <p>🔍 Se encontraron <strong>${productosMostrados}</strong> de <strong>${totalProductos}</strong> herramientas para "<strong>${this.filtroActual}</strong>"</p>
                `;
            }
        } else {
            // Sin filtros activos
            mensajeHTML = `
                <p>📋 Mostrando <strong>${productosMostrados}</strong> herramientas del inventario</p>
            `;
        }
        
        mensajeElement.innerHTML = mensajeHTML;
        container.appendChild(mensajeElement);
    }
    
    async mostrarQrProducto(productoId) {
        try {
            const producto = this.productos.find(p => p.id === productoId);
            if (!producto) return;
            
            // Mostrar loading
            document.getElementById('qrProductoImg').src = '';
            document.getElementById('qrProductoInfo').innerHTML = 'Cargando QR...';
            document.getElementById('qrModal').style.display = 'block';
            // Prevenir scroll del body
            document.body.classList.add('modal-open');
            
            const response = await fetch(`${this.apiUrl}/productos/${productoId}/qr`);
            if (!response.ok) throw new Error('No se pudo obtener el QR');
            
            const data = await response.json();
            
            // Mostrar información del producto
            document.getElementById('qrProductoInfo').innerHTML = `
                <div style="margin-bottom: 15px; text-align: left;">
                    <strong>Herramienta:</strong> ${producto.nombre}<br>
                    <strong>Código:</strong> ${producto.codigo_barras || 'N/A'}<br>
                    <strong>Ubicación:</strong> ${producto.ubicacion || 'N/A'}
                </div>
            `;
            
            // Mostrar QR
            document.getElementById('qrProductoImg').src = data.qr;
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('qrProductoInfo').innerHTML = 'Error al cargar el QR';
        }
    }
    
    cerrarQrModal() {
        document.getElementById('qrModal').style.display = 'none';
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    imprimirQr() {
        const printWindow = window.open('', '_blank');
        const qrImg = document.getElementById('qrProductoImg');
        const productoInfo = document.getElementById('qrProductoInfo').innerHTML;
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Imprimir Código QR - Longoria Tooling</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        text-align: center;
                    }
                    .qr-container {
                        margin: 20px 0;
                        padding: 10px;
                        border: 1px solid #ccc;
                        display: inline-block;
                    }
                    .producto-info {
                        margin-bottom: 15px;
                        text-align: left;
                        font-size: 12px;
                    }
                    img {
                        max-width: 100%;
                        height: auto;
                    }
                    @media print {
                        body { margin: 0; }
                        .qr-container { border: none; }
                    }
                </style>
            </head>
            <body>
                <div class="qr-container">
                    <div class="producto-info">${productoInfo}</div>
                    <img src="${qrImg.src}" alt="Código QR" />
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
            </html>
        `);
        printWindow.document.close();
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
                return false;
            }
            return true;
        } catch (error) {
            console.error('Error verificando sesión:', error);
            return false;
        }
    }
    
    // ===== SISTEMA DE TICKETS =====
    
    async initTickets() {
        // Solo inicializar tickets si el usuario tiene permisos
        if (this.currentUser && ['supervisor', 'operador', 'admin'].includes(this.currentUser.rol)) {
            // Para administradores, los tickets se cargarán cuando se seleccione la pestaña
            if (this.currentUser.rol !== 'admin') {
                this.loadTickets();
            }
            this.setupTicketEventListeners();
        } else {
            // Ocultar sección de tickets si no tiene permisos
            const ticketsSection = document.querySelector('.tickets-section');
            if (ticketsSection) {
                ticketsSection.style.display = 'none';
            }
        }
    }
    
    setupTicketEventListeners() {
        // Formulario de ticket
        const ticketForm = document.getElementById('ticketForm');
        if (ticketForm) {
            ticketForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.crearTicket();
            });
        }
        
        // Formulario de decisión
        const ticketDecisionForm = document.getElementById('ticketDecisionForm');
        if (ticketDecisionForm) {
            ticketDecisionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.procesarDecisionTicket();
            });
        }
        
        // Eventos de teclado para cerrar modales con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.cerrarModalActivo();
            }
        });
        
        // Eventos de clic fuera de modales para cerrarlos
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.cerrarModalActivo();
            }
        });
    }
    
    cerrarModalActivo() {
        // Cerrar el modal que esté actualmente abierto
        const modales = [
            'ticketModal',
            'ticketDetalleModal', 
            'ticketDecisionModal',
            'ticketEntregaModal',
            'qrModal',
            'confirmModal'
        ];
        
        for (const modalId of modales) {
            const modal = document.getElementById(modalId);
            if (modal && modal.style.display === 'flex') {
                modal.style.display = 'none';
                // Restaurar scroll del body
                document.body.classList.remove('modal-open');
                break; // Solo cerrar el primer modal que encuentre abierto
            }
        }
    }
    
    cerrarTodosLosModales() {
        // Cerrar todos los modales de tickets
        const modales = [
            'ticketModal',
            'ticketDetalleModal', 
            'ticketDecisionModal',
            'ticketEntregaModal'
        ];
        
        modales.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal && modal.style.display === 'flex') {
                modal.style.display = 'none';
            }
        });
        
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    async loadTickets() {
        try {
            const response = await fetch(`${this.apiUrl}/tickets`);
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            
            const data = await response.json();
            this.renderTickets(data.tickets);
        } catch (error) {
            console.error('Error cargando tickets:', error);
            this.showNotification('Error al cargar tickets', 'error');
        }
    }
    
    renderTickets(tickets) {
        const ticketsList = document.getElementById('ticketsList');
        if (!ticketsList) return;
        
        if (tickets.length === 0) {
            ticketsList.innerHTML = '<p style="text-align: center; color: #666; grid-column: 1/-1;">No hay tickets disponibles</p>';
            return;
        }
        
        ticketsList.innerHTML = tickets.map(ticket => this.renderTicketCard(ticket)).join('');
    }
    
    renderTicketCard(ticket) {
        const fecha = new Date(ticket.fecha_solicitud).toLocaleDateString('es-ES');
        const itemsHtml = ticket.items.map(item => `
            <div class="ticket-item">
                <div class="ticket-item-name">${item.producto_nombre}</div>
                <div class="ticket-item-qty">Cantidad: ${item.cantidad_solicitada}</div>
            </div>
        `).join('');
        
        const actionsHtml = this.renderTicketActions(ticket);
        
        return `
            <div class="ticket-card ${ticket.estado}" onclick="app.verTicketDetalle(${ticket.id})">
                <div class="ticket-header">
                    <div class="ticket-numero">${ticket.numero_ticket}</div>
                    <div class="ticket-estado ${ticket.estado}">${ticket.estado}</div>
                </div>
                
                <div class="ticket-info">
                    <p><strong>Orden:</strong> ${ticket.orden_produccion}</p>
                    <p><strong>Solicitante:</strong> ${ticket.solicitante_nombre}</p>
                    <p><strong>Fecha:</strong> ${fecha}</p>
                    <p><strong>Herramientas:</strong> ${ticket.total_items || ticket.items.length}</p>
                </div>
                
                <div class="ticket-items">
                    <h4>Herramientas solicitadas:</h4>
                    ${itemsHtml}
                </div>
                
                <div class="ticket-actions">
                    ${actionsHtml}
                </div>
            </div>
        `;
    }
    
    renderTicketActions(ticket) {
        const actions = [];
        
        console.log('🔍 Renderizando acciones para ticket:', {
            ticketId: ticket.id,
            estado: ticket.estado,
            solicitante_id: ticket.solicitante_id,
            currentUser: {
                id: this.currentUser.id,
                rol: this.currentUser.rol
            }
        });
        
        if (this.currentUser.rol === 'admin') {
            if (ticket.estado === 'pendiente') {
                actions.push('<button onclick="event.stopPropagation(); app.mostrarDecisionModal(' + ticket.id + ')" class="btn-primary">📋 Revisar</button>');
            } else if (ticket.estado === 'aprobado') {
                actions.push('<button onclick="event.stopPropagation(); app.mostrarEntregaModal(' + ticket.id + ')" class="btn-primary">📦 Entregar</button>');
            }
        }
        
        // Botón de devolución para supervisores y operadores en tickets entregados
        console.log('🔍 Verificando condiciones para botón de devolución:', {
            estadoEsEntregado: ticket.estado === 'entregado',
            usuarioEsSupervisorOOperador: ['supervisor', 'operador'].includes(this.currentUser.rol),
            usuarioEsSupervisor: this.currentUser.rol === 'supervisor',
            usuarioEsSolicitante: Number(ticket.solicitante_id) === Number(this.currentUser.id),
            solicitante_id: ticket.solicitante_id,
            currentUser_id: this.currentUser.id,
            solicitante_id_type: typeof ticket.solicitante_id,
            currentUser_id_type: typeof this.currentUser.id
        });
        
        if (ticket.estado === 'entregado' && ['supervisor', 'operador'].includes(this.currentUser.rol)) {
            // Verificar que el usuario sea el solicitante o supervisor
            if (this.currentUser.rol === 'supervisor' || Number(ticket.solicitante_id) === Number(this.currentUser.id)) {
                console.log('✅ Agregando botón de devolución para ticket', ticket.id);
                actions.push('<button onclick="event.stopPropagation(); app.mostrarDevolucionModal(' + ticket.id + ')" class="btn-secondary">🔄 Devolver</button>');
            } else {
                console.log('❌ No se agrega botón de devolución - usuario no es solicitante ni supervisor');
            }
        } else {
            console.log('❌ No se agrega botón de devolución - condiciones no cumplidas');
        }
        
        if (ticket.estado === 'pendiente' && Number(ticket.solicitante_id) === Number(this.currentUser.id)) {
            actions.push('<button onclick="event.stopPropagation(); app.cancelarTicket(' + ticket.id + ')" class="btn-danger">❌ Cancelar</button>');
        }
        
        console.log('🔍 Acciones generadas:', actions);
        return actions.join('');
    }
    
    mostrarFormularioTicket() {
        // Verificar permisos
        if (!['supervisor', 'operador'].includes(this.currentUser.rol)) {
            this.showNotification('Solo supervisores y operadores pueden crear tickets', 'error');
            return;
        }
        
        // Limpiar formulario
        document.getElementById('ticketForm').reset();
        document.getElementById('ticketItemsList').innerHTML = '';
        
        // Mostrar modal
        document.getElementById('ticketModal').style.display = 'flex';
        document.getElementById('ticketModalTitle').textContent = '🎫 Nuevo Ticket de Compra';
        // Prevenir scroll del body
        document.body.classList.add('modal-open');
    }
    
    agregarItemTicket() {
        const itemsList = document.getElementById('ticketItemsList');
        
        // Mostrar modal de escáner QR
        this.mostrarQrScannerModal();
    }
    
    mostrarQrScannerModal() {
        console.log('🔍 Verificando compatibilidad de cámara...');
        console.log('navigator.mediaDevices:', navigator.mediaDevices);
        console.log('navigator.mediaDevices.getUserMedia:', navigator.mediaDevices?.getUserMedia);
        console.log('Protocolo actual:', location.protocol);
        console.log('Hostname:', location.hostname);
        
        // Verificar si el navegador soporta getUserMedia
        if (!navigator.mediaDevices) {
            console.error('❌ navigator.mediaDevices no está disponible');
            this.showNotification('Su navegador no soporta el acceso a la cámara. Use Chrome, Firefox o Safari actualizado.', 'error');
            return;
        }
        
        if (!navigator.mediaDevices.getUserMedia) {
            console.error('❌ navigator.mediaDevices.getUserMedia no está disponible');
            this.showNotification('Su navegador no soporta getUserMedia. Use Chrome, Firefox o Safari actualizado.', 'error');
            return;
        }
        
        // Verificar si estamos en HTTPS (requerido para cámara en muchos navegadores)
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            console.error('❌ Protocolo no seguro:', location.protocol);
            this.showNotification('El acceso a la cámara requiere HTTPS. Use localhost para desarrollo.', 'error');
            return;
        }
        
        console.log('✅ Compatibilidad verificada, mostrando modal...');
        
        // Mostrar modal
        document.getElementById('qrScannerModal').style.display = 'flex';
        document.getElementById('scannerStatusText').textContent = '🔄 Listo para escanear';
        document.getElementById('qrScannerStatus').className = 'scanner-status';
        
        // Mostrar botón de iniciar escáner
        document.getElementById('startScannerBtn').style.display = 'inline-block';
        document.getElementById('stopScannerBtn').style.display = 'none';
        
        // Prevenir scroll del body
        document.body.classList.add('modal-open');
        
        // Mejoras específicas para móviles
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            console.log('📱 Detectado dispositivo móvil, aplicando optimizaciones...');
            
            // Forzar el scroll del modal después de un breve delay
            setTimeout(() => {
                const modalContent = document.querySelector('.qr-scanner-content');
                if (modalContent) {
                    modalContent.scrollTop = 0;
                    console.log('📱 Scroll del modal inicializado');
                }
            }, 100);
            
            // Agregar listener para orientación
            window.addEventListener('orientationchange', () => {
                setTimeout(() => {
                    const modalContent = document.querySelector('.qr-scanner-content');
                    if (modalContent) {
                        modalContent.scrollTop = 0;
                        console.log('📱 Scroll del modal reinicializado después del cambio de orientación');
                    }
                }, 300);
            });
        }
        
        // Aplicar mejoras de scroll para móviles
        setTimeout(() => {
            this.mejorarScrollMovil();
        }, 200);
    }
    
    async iniciarQrScanner() {
        try {
            const video = document.getElementById('qrVideo');
            const statusText = document.getElementById('scannerStatusText');
            const statusDiv = document.getElementById('qrScannerStatus');
            
            statusText.textContent = '🔐 Solicitando permisos de cámara...';
            statusDiv.className = 'scanner-status';
            
            // Verificar si ZXing está disponible
            if (typeof ZXing === 'undefined') {
                throw new Error('ZXing no está disponible. Verifique la conexión a internet.');
            }
            
            // Obtener acceso a la cámara
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Usar cámara trasera si está disponible
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            video.srcObject = stream;
            statusText.textContent = '🔍 Escaneando... Posicione el código QR frente a la cámara';
            statusDiv.className = 'scanner-status scanning';
            
            // Ocultar botón de iniciar y mostrar botón de detener
            document.getElementById('startScannerBtn').style.display = 'none';
            document.getElementById('stopScannerBtn').style.display = 'inline-block';
            
            // Inicializar ZXing
            this.zxingReader = new ZXing.BrowserQRCodeReader();
            
            // Iniciar escaneo
            this.iniciarEscaneoZXing(video);
            
        } catch (error) {
            console.error('Error accediendo a la cámara:', error);
            
            let mensajeError = 'Error al acceder a la cámara';
            let instrucciones = '';
            
            if (error.name === 'NotAllowedError') {
                mensajeError = 'Permiso de cámara denegado';
                instrucciones = 'Haga clic en "Permitir" cuando el navegador lo solicite. Si ya lo denegó, recargue la página.';
            } else if (error.name === 'NotFoundError') {
                mensajeError = 'No se encontró ninguna cámara';
                instrucciones = 'Verifique que su dispositivo tenga cámara y esté conectada.';
            } else if (error.name === 'NotReadableError') {
                mensajeError = 'La cámara está siendo usada por otra aplicación';
                instrucciones = 'Cierre otras aplicaciones que usen la cámara (WhatsApp, Zoom, etc.) y recargue la página.';
            } else if (error.name === 'OverconstrainedError') {
                mensajeError = 'La cámara no cumple con los requisitos';
                instrucciones = 'Intente usar un dispositivo diferente o actualice su navegador.';
            } else if (error.name === 'TypeError') {
                mensajeError = 'Error de configuración de la cámara';
                instrucciones = 'Verifique que su navegador esté actualizado.';
            } else if (error.message.includes('ZXing')) {
                mensajeError = 'Error cargando ZXing';
                instrucciones = 'Verifique su conexión a internet y recargue la página.';
            }
            
            this.showNotification(mensajeError + '. ' + instrucciones, 'error');
            document.getElementById('scannerStatusText').textContent = '❌ ' + mensajeError;
            document.getElementById('qrScannerStatus').className = 'scanner-status error';
        }
    }
    
    async iniciarEscaneoZXing(video) {
        try {
            // Decodificar una vez desde el dispositivo de video
            const result = await this.zxingReader.decodeOnceFromVideoDevice(
                undefined, // Usar la cámara por defecto
                'qrVideo'  // ID del elemento video
            );
            
            console.log('✅ Código QR detectado:', result.text);
            this.procesarCodigoQR(result.text);
            
        } catch (error) {
            console.error('Error en escaneo ZXing:', error);
            // Continuar escaneando
            setTimeout(() => {
                this.iniciarEscaneoZXing(video);
            }, 1000);
        }
    }
    
    detenerQrScanner() {
        const video = document.getElementById('qrVideo');
        if (video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null;
        }
        
        // Detener ZXing si está activo
        if (this.zxingReader) {
            this.zxingReader.reset();
            this.zxingReader = null;
        }
    }
    
    cerrarQrScannerModal() {
        this.detenerQrScanner();
        document.getElementById('qrScannerModal').style.display = 'none';
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    procesarCodigoQR(qrData) {
        try {
            console.log('🔍 Procesando código QR:', qrData);
            
            // Enviar código al backend para buscar el producto
            fetch(`${this.apiUrl}/productos/buscar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ codigo: qrData })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Producto no encontrado');
                }
                return response.json();
            })
            .then(data => {
                console.log('✅ Producto encontrado:', data.producto);
                this.productoEscaneado(data.producto);
            })
            .catch(error => {
                console.error('❌ Error buscando producto:', error);
                this.showNotification('Producto no encontrado en el inventario', 'error');
                // Continuar escaneando
                setTimeout(() => {
                    this.iniciarEscaneoZXing(document.getElementById('qrVideo'));
                }, 2000);
            });
            
        } catch (error) {
            console.error('Error procesando código QR:', error);
            this.showNotification('Error al procesar código QR', 'error');
        }
    }
    
    productoEscaneado(producto) {
        const statusText = document.getElementById('scannerStatusText');
        const statusDiv = document.getElementById('qrScannerStatus');
        
        statusText.textContent = `✅ Producto detectado: ${producto.nombre}`;
        statusDiv.className = 'scanner-status success';
        
        // Verificar si estamos en modo devolución
        const devolucionModal = document.getElementById('devolucionModal');
        if (devolucionModal && devolucionModal.style.display === 'flex') {
            // Modo devolución
            this.procesarDevolucionQR(producto);
        } else {
            // Modo creación de ticket
            this.agregarProductoAlTicket(producto);
        }
        
        // Cerrar el modal después de un momento
        setTimeout(() => {
            this.cerrarQrScannerModal();
        }, 1500);
    }
    
    agregarProductoAlTicket(producto) {
        const itemsList = document.getElementById('ticketItemsList');
        
        // Verificar si el producto ya existe en el ticket
        const existingItem = document.querySelector(`[data-producto-id="${producto.id}"]`);
        
        if (existingItem) {
            // Si el producto ya existe, incrementar la cantidad
            const cantidadInput = existingItem.querySelector('.cantidad-input');
            const currentQuantity = parseInt(cantidadInput.value) || 0;
            const newQuantity = currentQuantity + 1;
            
            cantidadInput.value = newQuantity;
            
            // Mostrar notificación de cantidad actualizada
            this.showNotification(`✅ ${producto.nombre} - Cantidad actualizada a ${newQuantity}`, 'success');
            
            // Efecto visual de actualización
            cantidadInput.style.backgroundColor = '#d4edda';
            setTimeout(() => {
                cantidadInput.style.backgroundColor = '';
            }, 500);
            
        } else {
            // Si el producto no existe, crear nueva entrada
            const itemId = Date.now();
            
            const itemHtml = `
                <div class="ticket-item-form" data-item-id="${itemId}" data-producto-id="${producto.id}">
                    <div class="input-row">
                        <div class="input-group">
                            <label>Herramienta:</label>
                            <input type="text" value="${producto.nombre}" readonly style="background: #f8f9fa;">
                        </div>
                        <div class="input-group">
                            <label>Cantidad:</label>
                            <input type="number" class="cantidad-input" min="1" value="1" required>
                        </div>
                        <div class="input-group">
                            <label>Precio Unit.:</label>
                            <input type="number" class="precio-input" min="0" step="0.01" value="${producto.precio_unitario || ''}" readonly style="background: #f8f9fa;">
                        </div>
                        <button type="button" class="btn-remove-item" onclick="app.removerItemTicket(${itemId})">❌</button>
                    </div>
                </div>
            `;
            
            itemsList.insertAdjacentHTML('beforeend', itemHtml);
            
            this.showNotification(`✅ ${producto.nombre} agregado al ticket`, 'success');
        }
    }
    
    removerItemTicket(itemId) {
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (itemElement) {
            itemElement.remove();
        }
    }
    
    async crearTicket() {
        try {
            console.log('🔍 Iniciando creación de ticket...');
            
            // Validar formulario
            const ordenProduccion = document.getElementById('ordenProduccion').value.trim();
            const justificacion = document.getElementById('justificacion').value.trim();
            
            console.log('📝 Datos del formulario:', { ordenProduccion, justificacion });
            
            if (!ordenProduccion || !justificacion) {
                this.showNotification('Por favor complete todos los campos obligatorios', 'error');
                return;
            }
            
            // Recolectar items (solo productos escaneados)
            const items = [];
            const itemForms = document.querySelectorAll('.ticket-item-form');
            
            console.log('🔍 Encontrados', itemForms.length, 'formularios de items');
            
            for (const form of itemForms) {
                console.log('🔍 Procesando formulario:', form);
                console.log('🔍 Data attributes:', form.dataset);
                
                const cantidadInput = form.querySelector('.cantidad-input');
                const precioInput = form.querySelector('.precio-input');
                
                console.log('🔍 Inputs encontrados:', { 
                    cantidadInput: cantidadInput ? 'Sí' : 'No',
                    precioInput: precioInput ? 'Sí' : 'No'
                });
                
                // Obtener el ID del producto desde el data attribute
                const productoId = parseInt(form.dataset.productoId);
                
                console.log('🔍 Producto ID extraído:', productoId);
                
                if (productoId && cantidadInput && cantidadInput.value) {
                    const item = {
                        producto_id: productoId,
                        cantidad_solicitada: parseInt(cantidadInput.value),
                        precio_unitario: precioInput && precioInput.value ? parseFloat(precioInput.value) : null
                    };
                    
                    console.log('✅ Item agregado:', item);
                    items.push(item);
                } else {
                    console.log('❌ Item no válido:', { 
                        productoId, 
                        cantidadInput: cantidadInput ? cantidadInput.value : 'No encontrado',
                        cantidadInputExists: !!cantidadInput
                    });
                }
            }
            
            console.log('📦 Total de items válidos:', items.length);
            
            if (items.length === 0) {
                this.showNotification('Debe agregar al menos una herramienta al ticket (escanee códigos QR)', 'error');
                return;
            }
            
            // Crear ticket
            const ticketData = {
                orden_produccion: ordenProduccion,
                justificacion: justificacion,
                items: items
            };
            
            console.log('📤 Enviando ticket:', ticketData);
            
            const response = await fetch(`${this.apiUrl}/tickets`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ticketData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al crear ticket');
            }
            
            const result = await response.json();
            this.showNotification(`Ticket ${result.numero_ticket} creado exitosamente`, 'success');
            this.cerrarTicketModal();
            this.loadTickets();
            
        } catch (error) {
            console.error('❌ Error creando ticket:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    cerrarTicketModal() {
        document.getElementById('ticketModal').style.display = 'none';
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    async verTicketDetalle(ticketId) {
        try {
            const response = await fetch(`${this.apiUrl}/tickets/${ticketId}`);
            if (!response.ok) throw new Error('Error al obtener ticket');
            
            const ticket = await response.json();
            this.mostrarTicketDetalle(ticket);
            
        } catch (error) {
            console.error('Error obteniendo ticket:', error);
            this.showNotification('Error al obtener detalles del ticket', 'error');
        }
    }
    
    mostrarTicketDetalle(ticket) {
        const fechaSolicitud = new Date(ticket.fecha_solicitud).toLocaleString('es-ES');
        const fechaAprobacion = ticket.fecha_aprobacion ? new Date(ticket.fecha_aprobacion).toLocaleString('es-ES') : 'N/A';
        const fechaEntrega = ticket.fecha_entrega ? new Date(ticket.fecha_entrega).toLocaleString('es-ES') : 'N/A';
        
        const itemsHtml = ticket.items.map(item => `
            <div class="ticket-item">
                <div class="ticket-item-name">${item.producto_nombre}</div>
                <div class="ticket-item-qty">
                    Solicitado: ${item.cantidad_solicitada} | 
                    Entregado: ${item.cantidad_entregada || 0}
                </div>
            </div>
        `).join('');
        
        const detalleInfo = document.getElementById('ticketDetalleInfo');
        detalleInfo.innerHTML = `
            <div class="ticket-info">
                <p><strong>Número:</strong> ${ticket.numero_ticket}</p>
                <p><strong>Orden de Producción:</strong> ${ticket.orden_produccion}</p>
                <p><strong>Justificación:</strong> ${ticket.justificacion}</p>
                <p><strong>Solicitante:</strong> ${ticket.solicitante_nombre} (${ticket.solicitante_rol})</p>
                <p><strong>Estado:</strong> <span class="ticket-estado ${ticket.estado}">${ticket.estado}</span></p>
                <p><strong>Fecha de Solicitud:</strong> ${fechaSolicitud}</p>
                ${ticket.aprobador_nombre ? `<p><strong>Aprobado por:</strong> ${ticket.aprobador_nombre} (${fechaAprobacion})</p>` : ''}
                ${ticket.comentarios_aprobador ? `<p><strong>Comentarios:</strong> ${ticket.comentarios_aprobador}</p>` : ''}
                ${ticket.entregado_por_nombre ? `<p><strong>Entregado por:</strong> ${ticket.entregado_por_nombre} (${fechaEntrega})</p>` : ''}
            </div>
            
            <div class="ticket-items">
                <h4>Herramientas:</h4>
                ${itemsHtml}
            </div>
        `;
        
        // Configurar botones de acción
        const actionsContainer = document.getElementById('ticketDetalleActions');
        actionsContainer.innerHTML = this.renderTicketActions(ticket);
        
        // Mostrar modal
        document.getElementById('ticketDetalleModal').style.display = 'flex';
        // Prevenir scroll del body
        document.body.classList.add('modal-open');
    }
    
    mostrarDecisionModal(ticketId) {
        this.currentTicketId = ticketId;
        document.getElementById('ticketDecisionModal').style.display = 'flex';
        document.getElementById('ticketDecisionForm').reset();
        // Prevenir scroll del body
        document.body.classList.add('modal-open');
    }
    
    cerrarDecisionModal() {
        document.getElementById('ticketDecisionModal').style.display = 'none';
        this.currentTicketId = null;
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    async procesarDecisionTicket() {
        try {
            const accion = document.getElementById('decisionAccion').value;
            const comentarios = document.getElementById('decisionComentarios').value;
            
            const response = await fetch(`${this.apiUrl}/tickets/${this.currentTicketId}/aprobar`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    accion: accion,
                    comentarios: comentarios
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al procesar ticket');
            }
            
            const result = await response.json();
            this.showNotification(`Ticket ${result.numero_ticket} ${accion} exitosamente`, 'success');
            this.cerrarDecisionModal();
            this.loadTickets();
            
        } catch (error) {
            console.error('Error procesando ticket:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    async mostrarEntregaModal(ticketId) {
        try {
            const response = await fetch(`${this.apiUrl}/tickets/${ticketId}`);
            if (!response.ok) throw new Error('Error al obtener ticket');
            
            const ticket = await response.json();
            this.currentTicketId = ticketId;
            
            const itemsHtml = ticket.items.map(item => `
                <div class="entrega-item">
                    <div class="entrega-item-header">
                        <div class="entrega-item-name">${item.producto_nombre}</div>
                        <div class="entrega-item-qty">Solicitado: ${item.cantidad_solicitada}</div>
                    </div>
                    <div class="entrega-input">
                        <label>Cantidad a entregar:</label>
                        <input type="number" class="entrega-cantidad" min="0" max="${item.cantidad_solicitada}" value="${item.cantidad_solicitada}" data-item-id="${item.id}">
                        <span>/ ${item.cantidad_solicitada}</span>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('ticketEntregaItems').innerHTML = itemsHtml;
            document.getElementById('ticketEntregaModal').style.display = 'flex';
            // Prevenir scroll del body
            document.body.classList.add('modal-open');
            
        } catch (error) {
            console.error('Error obteniendo ticket para entrega:', error);
            this.showNotification('Error al cargar ticket para entrega', 'error');
        }
    }
    
    cerrarEntregaModal() {
        document.getElementById('ticketEntregaModal').style.display = 'none';
        this.currentTicketId = null;
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    async procesarEntrega() {
        try {
            const items = [];
            const entregaInputs = document.querySelectorAll('.entrega-cantidad');
            
            for (const input of entregaInputs) {
                const cantidad = parseInt(input.value) || 0;
                if (cantidad > 0) {
                    items.push({
                        item_id: parseInt(input.dataset.itemId),
                        cantidad_entregada: cantidad
                    });
                }
            }
            
            if (items.length === 0) {
                this.showNotification('Debe especificar al menos una cantidad a entregar', 'error');
                return;
            }
            
            const response = await fetch(`${this.apiUrl}/tickets/${this.currentTicketId}/entregar`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: items
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al procesar entrega');
            }
            
            const result = await response.json();
            this.showNotification(`Entrega procesada exitosamente. ${result.items_entregados} herramientas entregadas`, 'success');
            this.cerrarEntregaModal();
            this.loadTickets();
            this.loadProductos(); // Recargar productos para actualizar inventario
            
        } catch (error) {
            console.error('Error procesando entrega:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    async cancelarTicket(ticketId) {
        try {
            const response = await fetch(`${this.apiUrl}/tickets/${ticketId}/cancelar`, {
                method: 'PUT'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al cancelar ticket');
            }
            
            this.showNotification('Ticket cancelado exitosamente', 'success');
            this.loadTickets();
            
        } catch (error) {
            console.error('Error cancelando ticket:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    async mostrarDevolucionModal(ticketId) {
        try {
            // Obtener detalles del ticket
            const response = await fetch(`${this.apiUrl}/tickets/${ticketId}`);
            if (!response.ok) throw new Error('Error al obtener ticket');
            
            const ticket = await response.json();
            this.currentTicketId = ticketId;
            
            // Mostrar modal de devolución
            document.getElementById('devolucionModal').style.display = 'flex';
            document.getElementById('devolucionTicketInfo').innerHTML = `
                <div class="ticket-info">
                    <p><strong>Ticket:</strong> ${ticket.numero_ticket}</p>
                    <p><strong>Orden:</strong> ${ticket.orden_produccion}</p>
                    <p><strong>Estado:</strong> <span class="ticket-estado ${ticket.estado}">${ticket.estado}</span></p>
                </div>
                <div class="devolucion-instructions">
                    <p>📱 Escanee el código QR de la herramienta que desea devolver</p>
                    <p>💡 Puede devolver parcialmente las herramientas entregadas</p>
                </div>
            `;
            
            // Prevenir scroll del body
            document.body.classList.add('modal-open');
            
        } catch (error) {
            console.error('Error mostrando modal de devolución:', error);
            this.showNotification('Error al cargar información del ticket', 'error');
        }
    }
    
    cerrarDevolucionModal() {
        document.getElementById('devolucionModal').style.display = 'none';
        this.currentTicketId = null;
        // Restaurar scroll del body
        document.body.classList.remove('modal-open');
    }
    
    async procesarDevolucionQR(producto) {
        try {
            if (!this.currentTicketId) {
                this.showNotification('Error: No hay ticket seleccionado', 'error');
                return;
            }
            
            // Mostrar modal de confirmación de cantidad
            this.mostrarConfirmacionDevolucion(producto);
            
        } catch (error) {
            console.error('Error procesando devolución:', error);
            this.showNotification('Error al procesar devolución', 'error');
        }
    }
    
    mostrarConfirmacionDevolucion(producto) {
        const modal = document.getElementById('confirmacionDevolucionModal');
        const infoDiv = document.getElementById('confirmacionDevolucionInfo');
        
        infoDiv.innerHTML = `
            <div class="producto-devolucion-info">
                <h4>🔄 Confirmar Devolución</h4>
                <p><strong>Herramienta:</strong> ${producto.nombre}</p>
                <p><strong>Cantidad a devolver:</strong></p>
                <input type="number" id="cantidadDevolver" min="1" value="1" class="cantidad-devolver-input">
                <p class="devolucion-note">💡 Ingrese la cantidad que desea devolver</p>
            </div>
        `;
        
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');
        
        // Guardar producto para usar en la confirmación
        this.productoDevolucion = producto;
    }
    
    cerrarConfirmacionDevolucion() {
        document.getElementById('confirmacionDevolucionModal').style.display = 'none';
        this.productoDevolucion = null;
        document.body.classList.remove('modal-open');
    }
    
    async confirmarDevolucion() {
        try {
            if (!this.currentTicketId || !this.productoDevolucion) {
                this.showNotification('Error: Información incompleta', 'error');
                return;
            }
            
            const cantidad = parseInt(document.getElementById('cantidadDevolver').value);
            if (!cantidad || cantidad <= 0) {
                this.showNotification('Por favor ingrese una cantidad válida', 'error');
                return;
            }
            
            const devolucionData = {
                codigo: `ID:${this.productoDevolucion.id}|Nombre:${this.productoDevolucion.nombre}`,
                cantidad: cantidad
            };
            
            const response = await fetch(`${this.apiUrl}/tickets/${this.currentTicketId}/devolver`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(devolucionData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al procesar devolución');
            }
            
            const result = await response.json();
            this.showNotification(result.mensaje, 'success');
            
            // Cerrar modales
            this.cerrarConfirmacionDevolucion();
            this.cerrarDevolucionModal();
            
            // Recargar tickets
            this.loadTickets();
            
        } catch (error) {
            console.error('Error confirmando devolución:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    cambiarSeccion(seccionId) {
        console.log('🔍 cambiarSeccion llamado con:', seccionId);
        
        // Actualizar pestañas activas
        const tabs = document.querySelectorAll('.menu-tab');
        tabs.forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.section === seccionId) {
                tab.classList.add('active');
            }
        });
        
        // Mostrar la sección seleccionada
        this.mostrarSeccion(seccionId);
    }
    
    mostrarSeccion(seccionId) {
        console.log('🔍 mostrarSeccion llamado con:', seccionId);
        
        // Ocultar todas las secciones removiendo la clase 'active'
        const secciones = document.querySelectorAll('.content-section');
        console.log('🔍 Secciones encontradas:', secciones.length);
        
        secciones.forEach(seccion => {
            console.log('🔍 Removiendo clase active de:', seccion.className);
            seccion.classList.remove('active');
        });
        
        // Mostrar la sección seleccionada agregando la clase 'active'
        const seccionActiva = document.querySelector(`.${seccionId}`);
        if (seccionActiva) {
            console.log('🔍 Agregando clase active a:', seccionActiva.className);
            seccionActiva.classList.add('active');
        } else {
            console.error('❌ No se encontró la sección:', seccionId);
        }
        
        // Cargar datos si es necesario
        if (seccionId === 'products-section') {
            this.loadProductos();
        } else if (seccionId === 'tickets-section') {
            this.loadTickets();
        }
    }
    
    // Función para mejorar el scroll en dispositivos móviles
    mejorarScrollMovil() {
        const modalContent = document.querySelector('.qr-scanner-content');
        if (!modalContent) return;
        
        // Detectar si es un dispositivo táctil
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        if (isTouchDevice) {
            console.log('📱 Dispositivo táctil detectado, aplicando mejoras de scroll...');
            
            // Prevenir el scroll del body cuando se hace scroll en el modal
            modalContent.addEventListener('touchstart', (e) => {
                e.stopPropagation();
            }, { passive: true });
            
            modalContent.addEventListener('touchmove', (e) => {
                e.stopPropagation();
            }, { passive: true });
            
            // Asegurar que el scroll funcione correctamente
            modalContent.style.webkitOverflowScrolling = 'touch';
            modalContent.style.overflowY = 'auto';
            
            // Forzar un reflow para asegurar que el scroll funcione
            modalContent.offsetHeight;
        }
    }
}

// Inicializar aplicación
const app = new AlmacenApp();

// Cerrar modal al hacer clic fuera
window.addEventListener('click', (event) => {
    const modal = document.getElementById('confirmModal');
    if (event.target === modal) {
        app.cerrarModal();
    }
}); 