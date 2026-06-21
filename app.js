// Global Application State
let appState = {
    allEvents: [],
    filteredEvents: [],
    selectedSources: new Set(),
    currentYear: 2026,
    currentMonth: 5, // 0-indexed (June is 5)
    viewMode: 'list', // 'grid' or 'list'
    searchQuery: '',
    startDate: '2026-06-20',
    endDate: '2026-10-18',
    selectedDate: null
};

// Source Configuration
const SOURCE_METADATA = {
    'first_avenue': { name: 'First Avenue', color: 'var(--clr-first-avenue)' },
    'grand_casino_arena': { name: 'Grand Casino Arena', color: 'var(--clr-grand-casino)' },
    'acme_comedy_club': { name: 'Acme Comedy Club', color: 'var(--clr-acme-comedy)' },
    'guthrie_theater': { name: 'Guthrie Theater', color: 'var(--clr-guthrie-theater)' },
    'minneapolis': { name: 'Minneapolis.org', color: 'var(--clr-minneapolis)' },
    'mn_united_fc': { name: 'MN United FC', color: 'var(--clr-mn-united-fc)' },
    'minnesota_twins': { name: 'Minnesota Twins', color: 'var(--clr-minnesota-twins)' },
    'target_center': { name: 'Target Center', color: 'var(--clr-target-center)' },
    'minnesota_orchestra': { name: 'Minnesota Orchestra', color: 'var(--clr-minnesota-orchestra)' },
    'hennepin_arts': { name: 'Hennepin Arts', color: 'var(--clr-hennepin-arts)' },
    'us_bank_stadium': { name: 'U.S. Bank Stadium', color: 'var(--clr-us-bank-stadium)' },
    'northrop_auditorium': { name: 'Northrop Auditorium', color: 'var(--clr-northrop-auditorium)' },
    'ordway_theater': { name: 'Ordway Theater', color: 'var(--clr-ordway-theater)' },
    'visit_stpaul': { name: 'Visit Saint Paul', color: 'var(--clr-visit-stpaul)' },
    'dakota_jazz_club': { name: 'Dakota Jazz Club', color: 'var(--clr-dakota-jazz-club)' },
    'berlin_jazz_club': { name: 'Berlin Jazz Club', color: 'var(--clr-berlin-jazz-club)' },
    'crooners': { name: 'Crooners Supper Club', color: 'var(--clr-crooners)' },
    'visit_duluth': { name: 'Visit Duluth', color: 'var(--clr-visit-duluth)' },
    'luminary_arts_center': { name: 'Luminary Arts Center', color: 'var(--clr-luminary-arts-center)' },
    'utepils_brewery': { name: 'Utepils Brewery', color: 'var(--clr-utepils-brewery)' },
    'pryes_brewing': { name: 'Pryes Brewing', color: 'var(--clr-pryes-brewing)' },
    'mncba_workshops': { name: 'MNCBA Workshops', color: 'var(--clr-mncba-workshops)' },
    'coch_cooking_classes': { name: 'CoCH Cooking Classes', color: 'var(--clr-coch-cooking-classes)' },
    'dame_errant_clay': { name: 'Dame Errant Clay', color: 'var(--clr-dame-errant-clay)' },
    'mpls_parks': { name: 'MPLS Parks & Rec', color: 'var(--clr-mpls-parks)' }
};

const DEFAULT_SOURCE_COLOR = 'var(--clr-minneapolis)';

// Dom Elements
const dom = {
    statsTotal: document.getElementById('stats-total'),
    searchInput: document.getElementById('search-input'),
    startDateFilter: document.getElementById('start-date-filter'),
    endDateFilter: document.getElementById('end-date-filter'),
    sourceFilterContainer: document.getElementById('source-filter-container'),
    clearSourcesBtn: document.getElementById('clear-sources-btn'),
    periodLabel: document.getElementById('period-display-label'),
    prevPeriodBtn: document.getElementById('prev-period-btn'),
    nextPeriodBtn: document.getElementById('next-period-btn'),
    viewGridBtn: document.getElementById('view-grid-btn'),
    viewListBtn: document.getElementById('view-list-btn'),
    calendarGridView: document.getElementById('calendar-grid-view'),
    listFeedView: document.getElementById('list-feed-view'),
    monthDaysContainer: document.getElementById('month-days-container'),
    listFeedContainer: document.getElementById('list-feed-container'),
    eventModal: document.getElementById('event-modal'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    modalVenueBadge: document.getElementById('modal-venue-badge'),
    modalGenreBadge: document.getElementById('modal-genre-badge'),
    modalTitle: document.getElementById('modal-event-title'),
    modalDate: document.getElementById('modal-date'),
    modalTime: document.getElementById('modal-time'),
    modalTimeContainer: document.getElementById('modal-time-container'),
    modalSupport: document.getElementById('modal-support'),
    modalSupportContainer: document.getElementById('modal-support-container'),
    modalArtistsContainer: document.getElementById('modal-artists-container'),
    modalTicketsLink: document.getElementById('modal-tickets-link'),
    sidebarPanel: document.getElementById('sidebar-panel'),
    sidebarBackdrop: document.getElementById('sidebar-backdrop'),
    mobileFilterBtn: document.getElementById('mobile-filter-btn'),
    sidebarMobileClose: document.getElementById('sidebar-mobile-close')
};

// Start Application
async function init() {
    // If mobile screen on load, force list mode
    if (window.innerWidth <= 768) {
        appState.viewMode = 'list';
    }
    
    setupEventListeners();
    await fetchEvents();
    populateSourceFilters();
    applyFilters();
}

// Fetch compiled events
async function fetchEvents() {
    try {
        const response = await fetch('events.json');
        if (!response.ok) throw new Error('Failed to load events.json');
        const data = await response.json();
        
        appState.allEvents = data.shows || [];
        appState.filteredEvents = [...appState.allEvents];
        
        // Populate all sources into the selected set initially
        const sources = new Set(appState.allEvents.map(s => s.source));
        appState.selectedSources = sources;
        
        dom.statsTotal.innerText = appState.allEvents.length;
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Event Listeners
function setupEventListeners() {
    // Search
    dom.searchInput.addEventListener('input', (e) => {
        appState.searchQuery = e.target.value.toLowerCase();
        applyFilters();
    });

    // Date Filters
    dom.startDateFilter.addEventListener('change', (e) => {
        appState.startDate = e.target.value;
        applyFilters();
    });
    dom.endDateFilter.addEventListener('change', (e) => {
        appState.endDate = e.target.value;
        applyFilters();
    });

    // View Toggles
    dom.viewGridBtn.addEventListener('click', () => toggleView('grid'));
    dom.viewListBtn.addEventListener('click', () => toggleView('list'));

    // Period Navigation
    dom.prevPeriodBtn.addEventListener('click', () => navigatePeriod(-1));
    dom.nextPeriodBtn.addEventListener('click', () => navigatePeriod(1));

    // Clear Sources Filter
    dom.clearSourcesBtn.addEventListener('click', () => {
        appState.selectedSources.clear();
        document.querySelectorAll('.source-item').forEach(el => el.classList.remove('active'));
        applyFilters();
    });

    // Close Modal
    dom.closeModalBtn.addEventListener('click', closeModal);
    dom.eventModal.addEventListener('click', (e) => {
        if (e.target === dom.eventModal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Mobile Sidebar Drawer Toggles
    const openSidebar = () => {
        dom.sidebarPanel.classList.add('open');
        dom.sidebarBackdrop.classList.remove('hidden');
        setTimeout(() => dom.sidebarBackdrop.classList.add('active'), 10);
    };

    const closeSidebar = () => {
        dom.sidebarPanel.classList.remove('open');
        dom.sidebarBackdrop.classList.remove('active');
        setTimeout(() => dom.sidebarBackdrop.classList.add('hidden'), 300);
    };

    dom.mobileFilterBtn.addEventListener('click', openSidebar);
    dom.sidebarMobileClose.addEventListener('click', closeSidebar);
    dom.sidebarBackdrop.addEventListener('click', closeSidebar);

    // Keep mobile state in sync on resize
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            if (appState.viewMode !== 'list') {
                toggleView('list');
            }
        } else {
            // Close mobile sidebar if returning to desktop sizes
            dom.sidebarPanel.classList.remove('open');
            dom.sidebarBackdrop.classList.add('hidden');
            dom.sidebarBackdrop.classList.remove('active');
        }
    });
}

// Populate Source Filters checklist
function populateSourceFilters() {
    // Sort sources alphabetically by display name
    const uniqueSources = Object.keys(SOURCE_METADATA).sort((a, b) =>
        SOURCE_METADATA[a].name.localeCompare(SOURCE_METADATA[b].name)
    );
    dom.sourceFilterContainer.innerHTML = '';
    
    uniqueSources.forEach(source => {
        const meta = getSourceMeta(source);
        const item = document.createElement('div');
        item.className = 'source-item active';
        item.dataset.source = source;
        item.innerHTML = `
            <div class="source-color-dot" style="background-color: ${meta.color}"></div>
            <div class="source-name">${meta.name}</div>
        `;
        
        item.addEventListener('click', () => {
            if (appState.selectedSources.has(source)) {
                appState.selectedSources.delete(source);
                item.classList.remove('active');
            } else {
                appState.selectedSources.add(source);
                item.classList.add('active');
            }
            applyFilters();
        });
        
        dom.sourceFilterContainer.appendChild(item);
    });
}

// View toggle helper
function toggleView(mode) {
    appState.viewMode = mode;
    if (mode === 'grid') {
        appState.selectedDate = null; // Clear day filter when going back to grid
        dom.viewGridBtn.classList.add('active');
        dom.viewListBtn.classList.remove('active');
        dom.calendarGridView.classList.remove('hidden');
        dom.listFeedView.classList.add('hidden');
        renderGrid();
    } else {
        dom.viewGridBtn.classList.remove('active');
        dom.viewListBtn.classList.add('active');
        dom.calendarGridView.classList.add('hidden');
        dom.listFeedView.classList.remove('hidden');
        renderList();
    }
}

// Month Navigation
function navigatePeriod(direction) {
    appState.selectedDate = null; // Clear day filter on month navigation
    appState.currentMonth += direction;
    if (appState.currentMonth < 0) {
        appState.currentMonth = 11;
        appState.currentYear -= 1;
    } else if (appState.currentMonth > 11) {
        appState.currentMonth = 0;
        appState.currentYear += 1;
    }
    
    if (appState.viewMode === 'grid') {
        renderGrid();
    } else {
        renderList();
    }
}

// Filter core logic
function applyFilters() {
    const start = new Date(appState.startDate);
    const end = new Date(appState.endDate);
    
    appState.filteredEvents = appState.allEvents.filter(show => {
        const sDate = new Date(show.date);
        const eDate = show.end_date ? new Date(show.end_date) : sDate;
        
        // 1. Source Filter
        if (!appState.selectedSources.has(show.source)) return false;
        
        // 2. Date Overlap Check
        if (sDate > end || eDate < start) return false;
        
        // 3. Search Filter
        if (appState.searchQuery) {
            const titleMatch = show.title.toLowerCase().includes(appState.searchQuery);
            const venueMatch = show.venue.toLowerCase().includes(appState.searchQuery);
            const artistMatch = show.artists && show.artists.some(a => a.toLowerCase().includes(appState.searchQuery));
            if (!titleMatch && !venueMatch && !artistMatch) return false;
        }
        
        return true;
    });

    dom.statsTotal.innerText = appState.filteredEvents.length;
    
    if (appState.viewMode === 'grid') {
        renderGrid();
    } else {
        renderList();
    }
}

// Helper: Get source metadata details
function getSourceMeta(source) {
    return SOURCE_METADATA[source] || { name: source, color: DEFAULT_SOURCE_COLOR };
}

// Render Calendar Grid View
function renderGrid() {
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    
    dom.periodLabel.innerText = `${monthNames[appState.currentMonth]} ${appState.currentYear}`;
    dom.monthDaysContainer.innerHTML = '';
    
    // Day calculations
    const firstDayIndex = new Date(appState.currentYear, appState.currentMonth, 1).getDay(); // Sunday=0
    // Shift Sunday from index 0 to 6 (so Monday=0, Sunday=6)
    const shiftedFirstDay = firstDayIndex === 0 ? 6 : firstDayIndex - 1;
    
    const totalDays = new Date(appState.currentYear, appState.currentMonth + 1, 0).getDate();
    const prevMonthDays = new Date(appState.currentYear, appState.currentMonth, 0).getDate();
    
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    // 1. Render Padding Days from previous month
    for (let i = shiftedFirstDay - 1; i >= 0; i--) {
        const day = prevMonthDays - i;
        const cell = document.createElement('div');
        cell.className = 'day-cell inactive';
        cell.innerHTML = `<div class="day-num-row"><span class="day-num">${day}</span></div>`;
        dom.monthDaysContainer.appendChild(cell);
    }
    
    // 2. Render Current Month Days
    for (let day = 1; day <= totalDays; day++) {
        const dateStr = `${appState.currentYear}-${String(appState.currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        const cell = document.createElement('div');
        cell.className = 'day-cell';
        if (dateStr === todayStr) {
            cell.classList.add('today');
        }
        
        // Find matching events for this specific day
        const dayEvents = appState.filteredEvents.filter(show => {
            const sDateStr = show.date;
            const eDateStr = show.end_date || show.date;
            return dateStr >= sDateStr && dateStr <= eDateStr;
        });
        
        const eventsListHtml = dayEvents.map(show => {
            const meta = getSourceMeta(show.source);
            return `
                <div class="grid-event-dot" 
                     style="background-color: ${meta.color}; color: ${meta.color};" 
                     data-id="${show.date}-${show.title}"
                     title="${show.title} @ ${show.venue}">
                </div>
            `;
        }).join('');
        
        cell.innerHTML = `
            <div class="day-num-row">
                <span class="day-num">${day}</span>
            </div>
            <div class="day-events-list">
                ${eventsListHtml}
            </div>
        `;
        
        // Add click events to open details modal
        cell.querySelectorAll('.grid-event-dot').forEach((dot, idx) => {
            dot.addEventListener('click', (e) => {
                e.stopPropagation();
                showDetailsModal(dayEvents[idx]);
            });
        });
        
        // Click on cell to switch to list view for only events on this day
        cell.addEventListener('click', () => {
            appState.selectedDate = dateStr;
            toggleView('list');
        });
        
        dom.monthDaysContainer.appendChild(cell);
    }
    
    // 3. Render Padding Days from next month (fill up grid to multiples of 7)
    const totalCells = shiftedFirstDay + totalDays;
    const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let day = 1; day <= remaining; day++) {
        const cell = document.createElement('div');
        cell.className = 'day-cell inactive';
        cell.innerHTML = `<div class="day-num-row"><span class="day-num">${day}</span></div>`;
        dom.monthDaysContainer.appendChild(cell);
    }
}

// Render List Feed View
function renderList() {
    dom.listFeedContainer.innerHTML = '';
    
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    
    let monthEvents = [];
    
    if (appState.selectedDate) {
        // Hide period navigation buttons
        dom.prevPeriodBtn.classList.add('hidden');
        dom.nextPeriodBtn.classList.add('hidden');
        
        // Format selected date nicely
        const dateObj = new Date(appState.selectedDate + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
        dom.periodLabel.innerHTML = `
            <span style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; color: var(--accent);" id="back-to-month-btn">
                <span class="material-symbols-outlined" style="font-size: 1.5rem;">arrow_back</span>
                ${formattedDate}
            </span>
        `;
        
        // Add back-to-grid listener
        document.getElementById('back-to-month-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            appState.selectedDate = null;
            toggleView('grid');
        });
        
        // Filter events matching only this date (supports date ranges)
        monthEvents = appState.filteredEvents.filter(show => {
            const sDate = show.date;
            const eDate = show.end_date || show.date;
            return appState.selectedDate >= sDate && appState.selectedDate <= eDate;
        });
    } else {
        // Show period navigation buttons
        dom.prevPeriodBtn.classList.remove('hidden');
        dom.nextPeriodBtn.classList.remove('hidden');
        
        dom.periodLabel.innerText = `${monthNames[appState.currentMonth]} ${appState.currentYear}`;
        
        // Filter events to only the active month
        const startMonthStr = `${appState.currentYear}-${String(appState.currentMonth + 1).padStart(2, '0')}-01`;
        const lastDayOfMonth = new Date(appState.currentYear, appState.currentMonth + 1, 0).getDate();
        const endMonthStr = `${appState.currentYear}-${String(appState.currentMonth + 1).padStart(2, '0')}-${lastDayOfMonth}`;
        
        monthEvents = appState.filteredEvents.filter(show => {
            const sDate = show.date;
            const eDate = show.end_date || show.date;
            return sDate <= endMonthStr && eDate >= startMonthStr;
        });
    }
    
    if (monthEvents.length === 0) {
        dom.listFeedContainer.innerHTML = `
            <div class="stat-card" style="text-align: center; padding: 3rem;">
                <span class="material-symbols-outlined" style="font-size: 3rem; color: var(--text-muted)">event_busy</span>
                <p style="margin-top: 1rem; color: var(--text-secondary)">No events scheduled for this period.</p>
            </div>
        `;
        return;
    }

    // Group shows by date
    const grouped = {};
    const startMonthStr = appState.selectedDate ? null : `${appState.currentYear}-${String(appState.currentMonth + 1).padStart(2, '0')}-01`;

    monthEvents.forEach(show => {
        // If the event starts before the current month, clamp it to the first of the month
        // so it groups under the current month instead of appearing in the previous month's header.
        const displayDate = (!appState.selectedDate && show.date < startMonthStr) ? startMonthStr : show.date;
        if (!grouped[displayDate]) grouped[displayDate] = [];
        grouped[displayDate].push(show);
    });

    // Render grouped dates chronologically
    const sortedDates = Object.keys(grouped).sort();
    sortedDates.forEach(dateStr => {
        const shows = grouped[dateStr];
        const dateObj = new Date(dateStr + 'T00:00:00');
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        
        const groupHeader = document.createElement('div');
        groupHeader.className = 'list-group-header';
        groupHeader.innerText = `${dayNames[dateObj.getDay()]}, ${monthNames[dateObj.getMonth()]} ${dateObj.getDate()}, ${dateObj.getFullYear()}`;
        dom.listFeedContainer.appendChild(groupHeader);
        
        shows.forEach(show => {
            const meta = getSourceMeta(show.source);
            const card = document.createElement('div');
            card.className = 'feed-event-card';
            
            // If the event started in a previous month, label it as Ongoing with the start date
            const isOngoing = show.date < dateStr;
            const subtitleText = isOngoing 
                ? `Ongoing (Started ${new Date(show.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })})`
                : (show.tour || 'Live Event');

            card.innerHTML = `
                <div class="card-date-col">
                    <div class="card-day-num">${dateObj.getDate()}</div>
                    <div class="card-month-year">${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}</div>
                    <div class="card-day-name">${dayNames[dateObj.getDay()]}</div>
                </div>
                <div class="card-info-col">
                    <span class="card-venue-badge" style="background-color: ${meta.color}20; color: ${meta.color}">
                        ${show.venue}
                    </span>
                    <h3 class="card-title">${show.title}</h3>
                    <p class="card-subtitle">${subtitleText}</p>
                </div>
                <div class="card-action-col">
                    <span class="material-symbols-outlined">chevron_right</span>
                </div>
            `;
            
            card.addEventListener('click', () => showDetailsModal(show));
            dom.listFeedContainer.appendChild(card);
        });
    });
}

// Open details popup
function showDetailsModal(show) {
    const meta = getSourceMeta(show.source);
    dom.modalVenueBadge.innerText = show.venue;
    dom.modalVenueBadge.style.backgroundColor = `${meta.color}20`;
    dom.modalVenueBadge.style.color = meta.color;
    
    // Genre / Type badge
    const isSports = show.venue.includes('Field') || show.title.includes('vs.');
    const isComedy = show.venue.includes('Comedy');
    dom.modalGenreBadge.innerText = isSports ? 'Sports' : (isComedy ? 'Comedy' : 'Concert / Show');
    
    dom.modalTitle.innerText = show.title;
    
    // Parse nice date
    const dateObj = new Date(show.date + 'T00:00:00');
    const fullDateStr = dateObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    
    if (show.end_date && show.end_date !== show.date) {
        const endDateObj = new Date(show.end_date + 'T00:00:00');
        const fullEndDateStr = endDateObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        dom.modalDate.innerText = `${fullDateStr} - ${fullEndDateStr}`;
    } else {
        dom.modalDate.innerText = fullDateStr;
    }
    
    // Performance time / tour details
    if (show.tour) {
        dom.modalTime.innerText = show.tour;
        dom.modalTimeContainer.classList.remove('hidden');
    } else {
        dom.modalTimeContainer.classList.add('hidden');
    }
    
    // Support/openers
    if (show.support_raw) {
        dom.modalSupport.innerText = show.support_raw;
        dom.modalSupportContainer.classList.remove('hidden');
    } else {
        dom.modalSupportContainer.classList.add('hidden');
    }
    
    // Artists Pills
    dom.modalArtistsContainer.innerHTML = '';
    const artists = show.artists || [show.title];
    artists.forEach(artist => {
        const pill = document.createElement('span');
        pill.className = 'artist-pill';
        pill.innerText = artist;
        dom.modalArtistsContainer.appendChild(pill);
    });
    
    // Tickets URL
    if (show.link) {
        dom.modalTicketsLink.href = show.link;
        dom.modalTicketsLink.classList.remove('hidden');
    } else {
        dom.modalTicketsLink.classList.add('hidden');
    }
    
    dom.eventModal.classList.remove('hidden');
    // Animate scale in
    dom.eventModal.querySelector('.modal-card').style.transform = 'scale(1)';
}

function closeModal() {
    dom.eventModal.querySelector('.modal-card').style.transform = 'scale(0.95)';
    dom.eventModal.classList.add('hidden');
}

// Start app
window.addEventListener('DOMContentLoaded', init);
