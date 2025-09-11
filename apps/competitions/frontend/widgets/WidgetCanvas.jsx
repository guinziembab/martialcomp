import React from 'react';
import { Draggable, Droppable } from 'react-beautiful-dnd';

const WidgetCanvas = ({ widgets, onWidgetClick, onWidgetDelete }) => {
    const widgetList = Object.entries(widgets).map(([id, widget]) => ({
        id,
        ...widget
    })).sort((a, b) => (a.order || 0) - (b.order || 0));

    const getWidgetIcon = (type) => {
        const icons = {
            contact_form: '📧',
            newsletter: '📬',
            countdown: '⏰',
            testimonials: '💬',
            social_feed: '📱',
            portfolio_filter: '🖼️',
            search: '🔍',
            calendar: '📅',
            pricing_table: '💰',
            team_filter: '👥'
        };
        return icons[type] || '📦';
    };

    const getWidgetTitle = (widget) => {
        return widget.config?.title || widget.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    return (
        <div className="widget-canvas">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h5>Ma page</h5>
                <div className="text-muted small">
                    {widgetList.length} widget{widgetList.length !== 1 ? 's' : ''} actif{widgetList.length !== 1 ? 's' : ''}
                </div>
            </div>

            {widgetList.length === 0 ? (
                <div className="empty-canvas">
                    <div className="text-center py-5">
                        <div className="empty-icon">📄</div>
                        <h6 className="mt-3">Aucun widget</h6>
                        <p className="text-muted">
                            Glissez-déposez des widgets depuis la palette pour commencer à construire votre page.
                        </p>
                    </div>
                </div>
            ) : (
                <Droppable droppableId="widget-canvas" type="WIDGET">
                    {(provided) => (
                        <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className="widget-list"
                        >
                            {widgetList.map((widget, index) => (
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
                                            className={`widget-card ${snapshot.isDragging ? 'dragging' : ''}`}
                                        >
                                            <div className="widget-header">
                                                <div className="widget-icon">
                                                    {getWidgetIcon(widget.type)}
                                                </div>
                                                <div className="widget-title">
                                                    {getWidgetTitle(widget)}
                                                </div>
                                                <div className="widget-actions">
                                                    <button
                                                        className="btn btn-sm btn-outline-primary"
                                                        onClick={() => onWidgetClick(widget.id)}
                                                        title="Configurer"
                                                    >
                                                        ⚙️
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-outline-danger"
                                                        onClick={() => onWidgetDelete(widget.id)}
                                                        title="Supprimer"
                                                    >
                                                        🗑️
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="widget-preview">
                                                <div className="preview-placeholder">
                                                    {widget.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </Draggable>
                            ))}
                            {provided.placeholder}
                        </div>
                    )}
                </Droppable>
            )}
        </div>
    );
};

export default WidgetCanvas; 