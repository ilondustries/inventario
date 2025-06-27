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
        
        if (formSection && mainContent) {
            if (this.currentUser && this.currentUser.rol === 'admin') {
                formSection.style.display = 'block';
                mainContent.classList.remove('form-hidden');
            } else {
                formSection.style.display = 'none';
                mainContent.classList.add('form-hidden');
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
                    <button onclick="app.mostrarQrProducto(${producto.id})" class="btn-qr" title="Ver QR">🔳 QR</button>
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
            this.loadTickets();
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
        
        if (this.currentUser.rol === 'admin') {
            if (ticket.estado === 'pendiente') {
                actions.push('<button onclick="event.stopPropagation(); app.mostrarDecisionModal(' + ticket.id + ')" class="btn-primary">📋 Revisar</button>');
            } else if (ticket.estado === 'aprobado') {
                actions.push('<button onclick="event.stopPropagation(); app.mostrarEntregaModal(' + ticket.id + ')" class="btn-primary">📦 Entregar</button>');
            }
        }
        
        if (ticket.estado === 'pendiente' && ticket.solicitante_id === this.currentUser.id) {
            actions.push('<button onclick="event.stopPropagation(); app.cancelarTicket(' + ticket.id + ')" class="btn-danger">❌ Cancelar</button>');
        }
        
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
    }
    
    agregarItemTicket() {
        const itemsList = document.getElementById('ticketItemsList');
        const itemId = Date.now(); // ID temporal
        
        const itemHtml = `
            <div class="ticket-item-form" data-item-id="${itemId}">
                <div class="input-row">
                    <div class="input-group">
                        <label>Herramienta:</label>
                        <select class="producto-select" required>
                            <option value="">Seleccionar herramienta...</option>
                            ${this.productos.map(p => `<option value="${p.id}" data-precio="${p.precio_unitario || 0}">${p.nombre}</option>`).join('')}
                        </select>
                    </div>
                    <div class="input-group">
                        <label>Cantidad:</label>
                        <input type="number" class="cantidad-input" min="1" value="1" required>
                    </div>
                    <div class="input-group">
                        <label>Precio Unit.:</label>
                        <input type="number" class="precio-input" min="0" step="0.01" placeholder="0.00">
                    </div>
                    <button type="button" class="btn-remove-item" onclick="app.removerItemTicket(${itemId})">❌</button>
                </div>
            </div>
        `;
        
        itemsList.insertAdjacentHTML('beforeend', itemHtml);
        
        // Configurar eventos para el nuevo item
        const itemElement = itemsList.querySelector(`[data-item-id="${itemId}"]`);
        const productoSelect = itemElement.querySelector('.producto-select');
        const precioInput = itemElement.querySelector('.precio-input');
        
        productoSelect.addEventListener('change', (e) => {
            const selectedOption = e.target.options[e.target.selectedIndex];
            const precio = selectedOption.dataset.precio;
            precioInput.value = precio || '';
        });
    }
    
    removerItemTicket(itemId) {
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (itemElement) {
            itemElement.remove();
        }
    }
    
    async crearTicket() {
        try {
            // Validar formulario
            const ordenProduccion = document.getElementById('ordenProduccion').value.trim();
            const justificacion = document.getElementById('justificacion').value.trim();
            
            if (!ordenProduccion || !justificacion) {
                this.showNotification('Por favor complete todos los campos obligatorios', 'error');
                return;
            }
            
            // Recolectar items
            const items = [];
            const itemForms = document.querySelectorAll('.ticket-item-form');
            
            for (const form of itemForms) {
                const productoSelect = form.querySelector('.producto-select');
                const cantidadInput = form.querySelector('.cantidad-input');
                const precioInput = form.querySelector('.precio-input');
                
                if (productoSelect.value && cantidadInput.value) {
                    items.push({
                        producto_id: parseInt(productoSelect.value),
                        cantidad_solicitada: parseInt(cantidadInput.value),
                        precio_unitario: precioInput.value ? parseFloat(precioInput.value) : null
                    });
                }
            }
            
            if (items.length === 0) {
                this.showNotification('Debe agregar al menos una herramienta al ticket', 'error');
                return;
            }
            
            // Crear ticket
            const ticketData = {
                orden_produccion: ordenProduccion,
                justificacion: justificacion,
                items: items
            };
            
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
            console.error('Error creando ticket:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    cerrarTicketModal() {
        document.getElementById('ticketModal').style.display = 'none';
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
    }
    
    mostrarDecisionModal(ticketId) {
        this.currentTicketId = ticketId;
        document.getElementById('ticketDecisionModal').style.display = 'flex';
        document.getElementById('ticketDecisionForm').reset();
    }
    
    cerrarDecisionModal() {
        document.getElementById('ticketDecisionModal').style.display = 'none';
        this.currentTicketId = null;
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
            
        } catch (error) {
            console.error('Error obteniendo ticket para entrega:', error);
            this.showNotification('Error al cargar ticket para entrega', 'error');
        }
    }
    
    cerrarEntregaModal() {
        document.getElementById('ticketEntregaModal').style.display = 'none';
        this.currentTicketId = null;
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
        if (!confirm('¿Está seguro de que desea cancelar este ticket?')) {
            return;
        }
        
        try {
            // Por ahora, solo permitimos cancelar tickets pendientes
            this.showNotification('Función de cancelación en desarrollo', 'info');
        } catch (error) {
            console.error('Error cancelando ticket:', error);
            this.showNotification('Error al cancelar ticket', 'error');
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