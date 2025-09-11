import React from 'react';
import { Draggable, Droppable } from 'react-beautiful-dnd';

const WidgetPalette = () => {
    const availableWidgets = [
        {
            id: 'contact_form',
            name: 'Formulaire de contact',
            description: 'Formulaire de contact avec validation',
            icon: '📧',
            category: 'Formulaires'
        },
        {
            id: 'newsletter',
            name: 'Newsletter',
            description: 'Inscription à la newsletter',
            icon: '📬',
            category: 'Formulaires'
        },
        {
            id: 'countdown',
            name: 'Compteur à rebours',
            description: 'Compteur pour événements',
            icon: '⏰',
            category: 'Événements'
        },
        {
            id: 'testimonials',
            name: 'Témoignages',
            description: 'Carrousel de témoignages',
            icon: '💬',
            category: 'Social'
        },
        {
            id: 'social_feed',
            name: 'Flux social',
            description: 'Affichage des réseaux sociaux',
            icon: '📱',
            category: 'Social'
        },
        {
            id: 'portfolio_filter',
            name: 'Filtre portfolio',
            description: 'Filtrage de portfolio par catégorie',
            icon: '🖼️',
            category: 'Portfolio'
        },
        {
            id: 'search',
            name: 'Recherche',
            description: 'Barre de recherche',
            icon: '🔍',
            category: 'Navigation'
        },
        {
            id: 'calendar',
            name: 'Calendrier',
            description: 'Calendrier d\'événements',
            icon: '📅',
            category: 'Événements'
        },
        {
            id: 'pricing_table',
            name: 'Tableau de prix',
            description: 'Affichage des tarifs',
            icon: '💰',
            category: 'Commerce'
        },
        {
            id: 'team_filter',
            name: 'Filtre équipe',
            description: 'Filtrage des membres d\'équipe',
            icon: '👥',
            category: 'Équipe'
        }
    ];

    const groupedWidgets = availableWidgets.reduce((acc, widget) => {
        if (!acc[widget.category]) {
            acc[widget.category] = [];
        }
        acc[widget.category].push(widget);
        return acc;
    }, {});

    return (
        <div className="widget-palette">
            <h5 className="mb-3">Widgets disponibles</h5>
            <p className="text-muted small mb-3">
                Glissez-déposez un widget vers la zone de droite pour l'ajouter à votre page.
            </p>
            
            {Object.entries(groupedWidgets).map(([category, widgets]) => (
                <div key={category} className="widget-category mb-4">
                    <h6 className="text-muted mb-2">{category}</h6>
                    <Droppable droppableId={category} type="PALETTE">
                        {(provided) => (
                            <div
                                ref={provided.innerRef}
                                {...provided.droppableProps}
                                className="widget-list"
                            >
                                {widgets.map((widget, index) => (
                                    <Draggable
                                        key={widget.id}
                                        draggableId={widget.id}
                                        index={index}
                                    >
                                        {(provided, snapshot) => (
                                            <div
                                                ref={provided.innerRef}
                                                {...provided.draggableProps}
                                                {...provided.dragHandleProps}
                                                className={`widget-item ${snapshot.isDragging ? 'dragging' : ''}`}
                                            >
                                                <div className="widget-icon">{widget.icon}</div>
                                                <div className="widget-info">
                                                    <div className="widget-name">{widget.name}</div>
                                                    <div className="widget-description">{widget.description}</div>
                                                </div>
                                            </div>
                                        )}
                                    </Draggable>
                                ))}
                                {provided.placeholder}
                            </div>
                        )}
                    </Droppable>
                </div>
            ))}
        </div>
    );
};

export default WidgetPalette; 