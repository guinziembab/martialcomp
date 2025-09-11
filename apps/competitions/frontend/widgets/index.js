import React from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext } from 'react-beautiful-dnd';
import WidgetBuilder from './WidgetBuilder';

// Récupérer l'ID de l'organisation depuis les données du template
const organizationId = window.organizationId || 1; // Fallback pour le développement

const App = () => {
    return (
        <DragDropContext>
            <WidgetBuilder organizationId={organizationId} />
        </DragDropContext>
    );
};

// Monter l'app React
const rootElement = document.getElementById('widget-builder-root');
if (rootElement) {
    ReactDOM.render(<App />, rootElement);
} else {
    console.error('Element #widget-builder-root non trouvé');
} 