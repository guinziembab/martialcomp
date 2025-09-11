import React, { useState, useEffect } from 'react';

const WidgetConfigModal = ({ widget, onSave, onClose }) => {
    const [config, setConfig] = useState(widget.config || {});

    useEffect(() => {
        setConfig(widget.config || {});
    }, [widget]);

    const handleInputChange = (field, value) => {
        setConfig(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(widget.id, config);
    };

    const renderConfigFields = () => {
        switch (widget.type) {
            case 'contact_form':
                return (
                    <>
                        <div className="mb-3">
                            <label className="form-label">Titre du formulaire</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.title || ''}
                                onChange={(e) => handleInputChange('title', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Texte du bouton</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.submit_text || ''}
                                onChange={(e) => handleInputChange('submit_text', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Message de succès</label>
                            <textarea
                                className="form-control"
                                rows="2"
                                value={config.success_message || ''}
                                onChange={(e) => handleInputChange('success_message', e.target.value)}
                            />
                        </div>
                    </>
                );

            case 'newsletter':
                return (
                    <>
                        <div className="mb-3">
                            <label className="form-label">Titre</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.title || ''}
                                onChange={(e) => handleInputChange('title', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Placeholder</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.placeholder || ''}
                                onChange={(e) => handleInputChange('placeholder', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Texte du bouton</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.submit_text || ''}
                                onChange={(e) => handleInputChange('submit_text', e.target.value)}
                            />
                        </div>
                    </>
                );

            case 'countdown':
                return (
                    <>
                        <div className="mb-3">
                            <label className="form-label">Titre</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.title || ''}
                                onChange={(e) => handleInputChange('title', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Date cible</label>
                            <input
                                type="datetime-local"
                                className="form-control"
                                value={config.target_date || ''}
                                onChange={(e) => handleInputChange('target_date', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <div className="form-check">
                                <input
                                    type="checkbox"
                                    className="form-check-input"
                                    checked={config.show_days || false}
                                    onChange={(e) => handleInputChange('show_days', e.target.checked)}
                                />
                                <label className="form-check-label">Afficher les jours</label>
                            </div>
                        </div>
                        <div className="mb-3">
                            <div className="form-check">
                                <input
                                    type="checkbox"
                                    className="form-check-input"
                                    checked={config.show_hours || false}
                                    onChange={(e) => handleInputChange('show_hours', e.target.checked)}
                                />
                                <label className="form-check-label">Afficher les heures</label>
                            </div>
                        </div>
                    </>
                );

            case 'testimonials':
                return (
                    <>
                        <div className="mb-3">
                            <label className="form-label">Titre</label>
                            <input
                                type="text"
                                className="form-control"
                                value={config.title || ''}
                                onChange={(e) => handleInputChange('title', e.target.value)}
                            />
                        </div>
                        <div className="mb-3">
                            <div className="form-check">
                                <input
                                    type="checkbox"
                                    className="form-check-input"
                                    checked={config.autoplay || false}
                                    onChange={(e) => handleInputChange('autoplay', e.target.checked)}
                                />
                                <label className="form-check-label">Lecture automatique</label>
                            </div>
                        </div>
                        <div className="mb-3">
                            <label className="form-label">Intervalle (ms)</label>
                            <input
                                type="number"
                                className="form-control"
                                value={config.interval || 5000}
                                onChange={(e) => handleInputChange('interval', parseInt(e.target.value))}
                            />
                        </div>
                    </>
                );

            default:
                return (
                    <div className="mb-3">
                        <label className="form-label">Titre</label>
                        <input
                            type="text"
                            className="form-control"
                            value={config.title || ''}
                            onChange={(e) => handleInputChange('title', e.target.value)}
                        />
                    </div>
                );
        }
    };

    return (
        <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1">
            <div className="modal-dialog modal-lg">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">
                            Configurer le widget : {widget.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </h5>
                        <button
                            type="button"
                            className="btn-close"
                            onClick={onClose}
                        ></button>
                    </div>
                    <form onSubmit={handleSubmit}>
                        <div className="modal-body">
                            {renderConfigFields()}
                        </div>
                        <div className="modal-footer">
                            <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={onClose}
                            >
                                Annuler
                            </button>
                            <button
                                type="submit"
                                className="btn btn-primary"
                            >
                                Enregistrer
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            <div className="modal-backdrop fade show"></div>
        </div>
    );
};

export default WidgetConfigModal; 