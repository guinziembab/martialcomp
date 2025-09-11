import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import WidgetPalette from './WidgetPalette';
import WidgetCanvas from './WidgetCanvas';
import WidgetConfigModal from './WidgetConfigModal';
import './styles.css';

const WidgetBuilder = ({ organizationId }) => {
    const [widgets, setWidgets] = useState({});
    const [selectedWidget, setSelectedWidget] = useState(null);
    const [showConfigModal, setShowConfigModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Charger la configuration des widgets depuis l'API
    useEffect(() => {
        loadWidgets();
    }, [organizationId]);

    const loadWidgets = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/admin/organizations/${organizationId}/widgets/api/`);
            if (response.ok) {
                const data = await response.json();
                setWidgets(data.widgets || {});
            } else {
                setError('Erreur lors du chargement des widgets');
            }
        } catch (err) {
            setError('Erreur de connexion');
        } finally {
            setLoading(false);
        }
    };

    const saveWidgets = async (newWidgets) => {
        try {
            const response = await fetch(`/admin/organizations/${organizationId}/widgets/api/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ widgets: newWidgets })
            });
            
            if (response.ok) {
                setWidgets(newWidgets);
                return true;
            } else {
                setError('Erreur lors de la sauvegarde');
                return false;
            }
        } catch (err) {
            setError('Erreur de connexion');
            return false;
        }
    };

    const handleDragEnd = async (result) => {
        const { source, destination, type } = result;

        if (!destination) return;

        if (type === 'WIDGET') {
            // Réorganisation des widgets
            const newWidgets = { ...widgets };
            const widgetIds = Object.keys(newWidgets);
            const [removed] = widgetIds.splice(source.index, 1);
            widgetIds.splice(destination.index, 0, removed);
            
            const reorderedWidgets = {};
            widgetIds.forEach(id => {
                reorderedWidgets[id] = newWidgets[id];
            });
            
            await saveWidgets(reorderedWidgets);
        } else if (type === 'PALETTE') {
            // Ajout d'un nouveau widget depuis la palette
            const widgetType = source.droppableId;
            const newWidgetId = `widget_${Date.now()}`;
            const newWidget = {
                type: widgetType,
                config: getDefaultConfig(widgetType),
                order: Object.keys(widgets).length
            };
            
            const newWidgets = { ...widgets, [newWidgetId]: newWidget };
            await saveWidgets(newWidgets);
        }
    };

    const handleWidgetClick = (widgetId) => {
        setSelectedWidget({ id: widgetId, ...widgets[widgetId] });
        setShowConfigModal(true);
    };

    const handleWidgetDelete = async (widgetId) => {
        const newWidgets = { ...widgets };
        delete newWidgets[widgetId];
        await saveWidgets(newWidgets);
    };

    const handleConfigSave = async (widgetId, config) => {
        const newWidgets = { ...widgets };
        newWidgets[widgetId] = { ...newWidgets[widgetId], config };
        await saveWidgets(newWidgets);
        setShowConfigModal(false);
        setSelectedWidget(null);
    };

    const getDefaultConfig = (widgetType) => {
        const configs = {
            contact_form: {
                title: 'Contactez-nous',
                submit_text: 'Envoyer',
                success_message: 'Message envoyé avec succès'
            },
            newsletter: {
                title: 'Restez informé',
                placeholder: 'Votre email',
                submit_text: 'S\'inscrire'
            },
            countdown: {
                title: 'Événement à venir',
                target_date: '',
                show_days: true,
                show_hours: true
            },
            testimonials: {
                title: 'Ce que disent nos clients',
                autoplay: true,
                interval: 5000
            }
        };
        return configs[widgetType] || {};
    };

    const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    };

    if (loading) {
        return (
            <div className="text-center py-5">
                <div className="spinner-border" role="status">
                    <span className="visually-hidden">Chargement...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-danger" role="alert">
                {error}
            </div>
        );
    }

    return (
        <div className="widget-builder">
            <div className="row">
                <div className="col-md-3">
                    <WidgetPalette />
                </div>
                <div className="col-md-9">
                    <WidgetCanvas
                        widgets={widgets}
                        onWidgetClick={handleWidgetClick}
                        onWidgetDelete={handleWidgetDelete}
                    />
                </div>
            </div>

            <DragDropContext onDragEnd={handleDragEnd}>
                {/* Zone de drop pour les widgets depuis la palette */}
                <Droppable droppableId="widget-canvas" type="PALETTE">
                    {(provided) => (
                        <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className="widget-drop-zone"
                        >
                            {provided.placeholder}
                        </div>
                    )}
                </Droppable>
            </DragDropContext>

            {showConfigModal && selectedWidget && (
                <WidgetConfigModal
                    widget={selectedWidget}
                    onSave={handleConfigSave}
                    onClose={() => {
                        setShowConfigModal(false);
                        setSelectedWidget(null);
                    }}
                />
            )}
        </div>
    );
};

export default WidgetBuilder; 