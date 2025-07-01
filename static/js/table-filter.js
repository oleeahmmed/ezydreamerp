/**
 * Advanced Table Filter System
 * A JavaScript solution focused on table filtering with auto-detection
 * and rich filtering capabilities
 */

class AdvancedTableFilter {
    constructor(tableId, options = {}) {
        console.log(`Initializing AdvancedTableFilter for tableId: ${tableId}`);
        this.table = document.getElementById(tableId);
        if (!this.table) {
            console.error(`Table with ID ${tableId} not found`);
            return;
        }
        this.tbody = this.table.querySelector('tbody');
        this.thead = this.table.querySelector('thead');
        if (!this.tbody || !this.thead) {
            console.error('Table is missing thead or tbody');
            return;
        }
        
        // Configuration options
        this.options = {
            enableGlobalSearch: true,
            autoDetectTypes: true,
            filterDelay: 300,
            ...options
        };
        
        // Internal state
        this.filters = new Map();
        this.activeFilters = new Map();
        this.filteredRows = [];
        this.allRows = [];
        this.columns = [];
        this.filterTimeout = null;
        
        this.init();
    }
    
    init() {
        console.log('Starting initialization');
        this.setupColumns();
        this.setupRows();
        this.createFilterInterface();
        this.setupEventListeners();
        this.updateActiveFiltersDisplay();
        
        // Initial filter
        this.applyFilters();
        console.log('Initialization complete');
    }
    
    setupColumns() {
        const headers = this.thead.querySelectorAll('th');
        console.log(`Found ${headers.length} columns in thead`);
        this.columns = Array.from(headers).map((th, index) => {
            const column = {
                index,
                name: th.dataset.column || th.textContent.trim().toLowerCase().replace(/\s+/g, '_'),
                displayName: th.textContent.trim(),
                type: th.dataset.type || this.detectColumnType(index),
                element: th
            };
            console.log(`Column ${index}: name=${column.name}, type=${column.type}`);
            return column;
        });
    }
    
    setupRows() {
        this.allRows = Array.from(this.tbody.querySelectorAll('tr')).map((row, index) => ({
            index,
            element: row,
            cells: Array.from(row.querySelectorAll('td')),
            data: Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim()),
            visible: true
        }));
        console.log(`Found ${this.allRows.length} rows in tbody`);
        this.filteredRows = [...this.allRows];
    }
    
    detectColumnType(columnIndex) {
        if (!this.options.autoDetectTypes) return 'text';
        
        const samples = this.allRows.slice(0, 10).map(row => row.data[columnIndex]);
        console.log(`Detecting type for column ${columnIndex}, samples:`, samples);
        
        // Check for numbers
        if (samples.every(val => !isNaN(val) && !isNaN(parseFloat(val)))) {
            console.log(`Column ${columnIndex} detected as number`);
            return 'number';
        }
        
        // Check for dates
        if (samples.every(val => !isNaN(Date.parse(val)) && !val.includes(':'))) {
            console.log(`Column ${columnIndex} detected as date`);
            return 'date';
        }
        
        // Check for datetime (e.g., "2025-07-01 09:00")
        if (samples.every(val => !isNaN(Date.parse(val)) && val.includes(':'))) {
            console.log(`Column ${columnIndex} detected as datetime`);
            return 'datetime';
        }
        
        // Check for limited unique values (potential select)
        const uniqueValues = [...new Set(samples)];
        if (uniqueValues.length <= Math.min(10, samples.length * 0.5)) {
            console.log(`Column ${columnIndex} detected as select, unique values:`, uniqueValues);
            return 'select';
        }
        
        console.log(`Column ${columnIndex} detected as text`);
        return 'text';
    }
    
    createFilterInterface() {
        const filterContainer = document.getElementById('filterContainer');
        if (!filterContainer) {
            console.error('filterContainer not found');
            return;
        }
        console.log('Creating filter interface');
        
        filterContainer.innerHTML = ''; // Clear existing content
        this.columns.forEach(col => {
            if (col.name !== 'checkbox') { // Skip checkbox column
                const filterGroup = this.createFilterGroup(col);
                filterContainer.appendChild(filterGroup);
                console.log(`Added filter group for column: ${col.name}`);
            }
        });
    }
    
    createFilterGroup(column) {
        const group = document.createElement('div');
        group.className = 'filter-group';
        group.dataset.column = column.name;
        
        const label = document.createElement('label');
        label.textContent = column.displayName;
        label.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';
        
        group.appendChild(label);
        
        let filterElement;
        
        switch (column.type) {
            case 'select':
                filterElement = this.createSelectFilter(column);
                break;
            case 'number':
                filterElement = this.createRangeFilter(column, 'number');
                break;
            case 'date':
            case 'datetime':
                filterElement = this.createRangeFilter(column, 'date');
                break;
            default:
                filterElement = this.createTextFilter(column);
        }
        
        group.appendChild(filterElement);
        return group;
    }
    
    createTextFilter(column) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'filter-input w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300';
        input.placeholder = `Filter by ${column.displayName.toLowerCase()}...`;
        input.dataset.column = column.name;
        input.dataset.type = 'text';
        
        input.addEventListener('input', (e) => {
            this.debounceFilter(() => {
                this.setFilter(column.name, 'text', e.target.value);
            });
        });
        
        return input;
    }
    
    createSelectFilter(column) {
        const select = document.createElement('select');
        select.className = 'filter-input w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300';
        select.dataset.column = column.name;
        select.dataset.type = 'select';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'All';
        select.appendChild(defaultOption);
        
        // Get unique values
        const uniqueValues = [...new Set(this.allRows.map(row => row.data[column.index]))];
        uniqueValues.sort().forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            this.setFilter(column.name, 'select', e.target.value);
        });
        
        return select;
    }
    
    createRangeFilter(column, type) {
        const container = document.createElement('div');
        container.className = 'range-inputs flex space-x-2';
        
        const minInput = document.createElement('input');
        minInput.type = type === 'date' ? 'date' : 'number';
        minInput.className = 'filter-input w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300';
        minInput.placeholder = 'Min';
        minInput.dataset.column = column.name;
        minInput.dataset.type = 'range-min';
        minInput.dataset.valueType = type;
        
        const separator = document.createElement('span');
        separator.className = 'range-separator text-gray-500 dark:text-gray-400 self-center';
        separator.textContent = '—';
        
        const maxInput = document.createElement('input');
        maxInput.type = type === 'date' ? 'date' : 'number';
        maxInput.className = 'filter-input w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300';
        maxInput.placeholder = 'Max';
        maxInput.dataset.column = column.name;
        maxInput.dataset.type = 'range-max';
        maxInput.dataset.valueType = type;
        
        [minInput, maxInput].forEach(input => {
            input.addEventListener('input', () => {
                this.debounceFilter(() => {
                    const minVal = minInput.value;
                    const maxVal = maxInput.value;
                    this.setFilter(column.name, 'range', { min: minVal, max: maxVal, type });
                });
            });
        });
        
        container.appendChild(minInput);
        container.appendChild(separator);
        container.appendChild(maxInput);
        
        return container;
    }
    
    setFilter(columnName, filterType, value) {
        console.log(`Setting filter for ${columnName}: type=${filterType}, value=`, value);
        if (this.isEmptyFilter(value)) {
            this.activeFilters.delete(columnName);
        } else {
            this.activeFilters.set(columnName, { type: filterType, value, columnName });
        }
        
        this.applyFilters();
        this.updateActiveFiltersDisplay();
    }
    
    isEmptyFilter(value) {
        if (!value) return true;
        if (typeof value === 'object' && (!value.min && !value.max)) return true;
        return false;
    }
    
    applyFilters() {
        console.log('Applying filters:', Array.from(this.activeFilters.entries()));
        this.filteredRows = this.allRows.filter(row => {
            return Array.from(this.activeFilters.values()).every(filter => {
                return this.passesFilter(row, filter);
            });
        });
        
        // Apply global search if enabled
        const globalSearch = document.getElementById('globalSearch');
        if (this.options.enableGlobalSearch && globalSearch && globalSearch.value) {
            console.log(`Applying global search: ${globalSearch.value}`);
            this.applyGlobalSearch(globalSearch.value);
        }
        
        this.updateDisplay();
    }
    
    passesFilter(row, filter) {
        const column = this.columns.find(col => col.name === filter.columnName);
        const cellValue = row.data[column.index];
        
        switch (filter.type) {
            case 'text':
                return cellValue.toLowerCase().includes(filter.value.toLowerCase());
                
            case 'select':
                return cellValue === filter.value;
                
            case 'range':
                return this.passesRangeFilter(cellValue, filter.value);
                
            default:
                return true;
        }
    }
    
    passesRangeFilter(cellValue, range) {
        let value = cellValue;
        
        if (range.type === 'number') {
            value = parseFloat(cellValue);
            const min = range.min ? parseFloat(range.min) : -Infinity;
            const max = range.max ? parseFloat(range.max) : Infinity;
            return value >= min && value <= max;
        } else if (range.type === 'date' || range.type === 'datetime') {
            const date = new Date(cellValue);
            const minDate = range.min ? new Date(range.min) : new Date('1900-01-01');
            const maxDate = range.max ? new Date(range.max) : new Date('2100-01-01');
            return date >= minDate && date <= maxDate;
        }
        
        return true;
    }
    
    applyGlobalSearch(searchTerm) {
        const term = searchTerm.toLowerCase();
        this.filteredRows = this.filteredRows.filter(row => {
            return row.data.some(cellValue => 
                cellValue.toLowerCase().includes(term)
            );
        });
    }
    
    updateDisplay() {
        console.log(`Updating display with ${this.filteredRows.length} filtered rows`);
        // Hide all rows first
        this.allRows.forEach(row => {
            row.element.style.display = 'none';
            row.element.classList.add('filtered-out');
        });
        
        // Show filtered rows
        this.filteredRows.forEach(row => {
            row.element.style.display = '';
            row.element.classList.remove('filtered-out');
        });
        
        this.updateActiveFiltersDisplay();
    }
    
    updateActiveFiltersDisplay() {
        const container = document.getElementById('activeFilters');
        if (!container) {
            console.warn('activeFilters container not found');
            return;
        }
        
        container.innerHTML = '';
        
        this.activeFilters.forEach((filter, columnName) => {
            const chip = document.createElement('div');
            chip.className = 'filter-chip inline-flex items-center bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1.5 rounded-full shadow-md hover:bg-blue-200 dark:hover:bg-blue-800 transition duration-200';
            
            const text = this.getFilterDisplayText(filter);
            chip.innerHTML = `
                <span class="text-sm">${text}</span>
                <button class="remove-filter ml-2 text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-100 focus:outline-none" data-column="${columnName}">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            `;
            
            chip.querySelector('.remove-filter').addEventListener('click', () => {
                this.removeFilter(columnName);
            });
            
            container.appendChild(chip);
        });
        console.log(`Updated active filters display with ${this.activeFilters.size} filters`);
    }
    
    getFilterDisplayText(filter) {
        const column = this.columns.find(col => col.name === filter.columnName);
        
        switch (filter.type) {
            case 'text':
                return `${column.displayName}: "${filter.value}"`;
            case 'select':
                return `${column.displayName}: ${filter.value}`;
            case 'range':
                let rangeText = column.displayName + ': ';
                if (filter.value.min && filter.value.max) {
                    rangeText += `${filter.value.min} - ${filter.value.max}`;
                } else if (filter.value.min) {
                    rangeText += `≥ ${filter.value.min}`;
                } else if (filter.value.max) {
                    rangeText += `≤ ${filter.value.max}`;
                }
                return rangeText;
            default:
                return `${column.displayName}: ${filter.value}`;
        }
    }
    
    removeFilter(columnName) {
        console.log(`Removing filter for ${columnName}`);
        this.activeFilters.delete(columnName);
        
        // Clear the filter input
        const filterGroup = document.querySelector(`[data-column="${columnName}"]`);
        if (filterGroup) {
            const inputs = filterGroup.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.value = '';
            });
        }
        
        this.applyFilters();
        this.updateActiveFiltersDisplay();
    }
    
    clearAllFilters() {
        console.log('Clearing all filters');
        this.activeFilters.clear();
        
        // Clear all filter inputs
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach(input => {
            input.value = '';
        });
        
        // Clear global search
        const globalSearch = document.getElementById('globalSearch');
        if (globalSearch) globalSearch.value = '';
        
        this.applyFilters();
        this.updateActiveFiltersDisplay();
    }
    
    setupEventListeners() {
        console.log('Setting up event listeners');
        // Clear all filters button
        const clearAllBtn = document.getElementById('clearAllFilters');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllFilters());
        } else {
            console.warn('clearAllFilters button not found');
        }
        
        // Toggle filters button
        const toggleBtn = document.getElementById('toggleFilters');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const filterControls = document.querySelector('.filter-controls');
                if (filterControls) {
                    filterControls.classList.toggle('hidden');
                }
            });
        } else {
            console.warn('toggleFilters button not found');
        }
        
        // Global search
        const globalSearch = document.getElementById('globalSearch');
        if (globalSearch && this.options.enableGlobalSearch) {
            globalSearch.addEventListener('input', (e) => {
                this.debounceFilter(() => {
                    this.applyFilters();
                });
            });
        } else {
            console.warn('globalSearch input not found or global search disabled');
        }
    }
    
    debounceFilter(callback) {
        clearTimeout(this.filterTimeout);
        this.filterTimeout = setTimeout(callback, this.options.filterDelay);
    }
    
    // Public API methods
    getFilteredData() {
        return this.filteredRows.map(row => {
            const rowData = {};
            this.columns.forEach((col, index) => {
                rowData[col.name] = row.data[index];
            });
            return rowData;
        });
    }
    
    addRow(rowData) {
        const tr = document.createElement('tr');
        this.columns.forEach(col => {
            const td = document.createElement('td');
            td.textContent = rowData[col.name] || '';
            tr.appendChild(td);
        });
        
        this.tbody.appendChild(tr);
        this.setupRows(); // Refresh rows
        this.applyFilters();
        console.log('Added new row');
    }
    
    removeRow(index) {
        if (this.allRows[index]) {
            this.allRows[index].element.remove();
            this.setupRows(); // Refresh rows
            this.applyFilters();
            console.log(`Removed row at index ${index}`);
        }
    }
    
    refresh() {
        this.setupRows();
        this.applyFilters();
        console.log('Refreshed table');
    }
}