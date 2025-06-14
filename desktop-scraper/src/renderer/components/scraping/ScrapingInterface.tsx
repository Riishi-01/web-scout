import React, { useState } from 'react';

interface ScrapingConfig {
  url: string;
  maxPages: number;
  attributes: string[];
  filters: {
    selector: string;
    value: string;
    action: 'click' | 'input' | 'select';
  }[];
  outputFormat: 'gsheets' | 'csv' | 'json';
  gsheetsPath?: string;
  requestDelay: number;
}

interface ScrapingStep {
  id: number;
  title: string;
  completed: boolean;
  active: boolean;
}

export const ScrapingInterface: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<ScrapingConfig>({
    url: '',
    maxPages: 10,
    attributes: ['title', 'price', 'description'],
    filters: [],
    outputFormat: 'gsheets',
    requestDelay: 1000
  });

  const [previewData, setPreviewData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const steps: ScrapingStep[] = [
    { id: 1, title: '🎯 URL & Target Setup', completed: currentStep > 1, active: currentStep === 1 },
    { id: 2, title: '🔧 Configure Attributes', completed: currentStep > 2, active: currentStep === 2 },
    { id: 3, title: '⚙️ Filters & Pages', completed: currentStep > 3, active: currentStep === 3 },
    { id: 4, title: '📊 Preview & Export', completed: currentStep > 4, active: currentStep === 4 },
    { id: 5, title: '🚀 Execute Scraping', completed: false, active: currentStep === 5 }
  ];

  const sampleTemplates = [
    {
      name: 'E-commerce Products',
      attributes: ['title', 'price', 'rating', 'reviews', 'availability'],
      description: 'Extract product information from online stores'
    },
    {
      name: 'Job Listings',
      attributes: ['job_title', 'company', 'location', 'salary', 'posted_date'],
      description: 'Scrape job postings and career information'
    },
    {
      name: 'Real Estate',
      attributes: ['property_title', 'price', 'bedrooms', 'bathrooms', 'location'],
      description: 'Extract property listings and details'
    },
    {
      name: 'News Articles',
      attributes: ['headline', 'author', 'publish_date', 'content', 'category'],
      description: 'Gather news articles and metadata'
    }
  ];

  const handleTemplateSelect = (template: typeof sampleTemplates[0]) => {
    setConfig(prev => ({
      ...prev,
      attributes: template.attributes
    }));
  };

  const addAttribute = () => {
    setConfig(prev => ({
      ...prev,
      attributes: [...prev.attributes, '']
    }));
  };

  const updateAttribute = (index: number, value: string) => {
    setConfig(prev => ({
      ...prev,
      attributes: prev.attributes.map((attr, i) => i === index ? value : attr)
    }));
  };

  const removeAttribute = (index: number) => {
    setConfig(prev => ({
      ...prev,
      attributes: prev.attributes.filter((_, i) => i !== index)
    }));
  };

  const addFilter = () => {
    setConfig(prev => ({
      ...prev,
      filters: [...prev.filters, { selector: '', value: '', action: 'click' }]
    }));
  };

  const updateFilter = (index: number, field: keyof typeof config.filters[0], value: string) => {
    setConfig(prev => ({
      ...prev,
      filters: prev.filters.map((filter, i) => 
        i === index ? { ...filter, [field]: value } : filter
      )
    }));
  };

  const removeFilter = (index: number) => {
    setConfig(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== index)
    }));
  };

  const generatePreview = async () => {
    setIsLoading(true);
    try {
      // Simulate preview generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockData = Array.from({ length: 5 }, (_, i) => {
        const data: any = {};
        config.attributes.forEach(attr => {
          if (attr === 'title') data[attr] = `Sample Product ${i + 1}`;
          else if (attr === 'price') data[attr] = `$${(Math.random() * 100 + 10).toFixed(2)}`;
          else if (attr === 'rating') data[attr] = `${(Math.random() * 2 + 3).toFixed(1)}/5`;
          else if (attr === 'description') data[attr] = `Sample description for item ${i + 1}`;
          else data[attr] = `Sample ${attr} ${i + 1}`;
        });
        return data;
      });
      
      setPreviewData(mockData);
    } catch (error) {
      console.error('Preview generation failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startScraping = async () => {
    setCurrentStep(5);
    setProgress(0);
    
    // Simulate scraping progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + Math.random() * 10;
      });
    }, 500);
  };

  const stepContainerStyle: React.CSSProperties = {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: '12px',
    padding: '24px',
    border: '1px solid var(--border-primary)',
    marginBottom: '24px'
  };

  const buttonStyle: React.CSSProperties = {
    backgroundColor: 'var(--accent-primary)',
    color: 'var(--accent-text)',
    border: 'none',
    borderRadius: '6px',
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease'
  };

  const inputStyle: React.CSSProperties = {
    backgroundColor: 'var(--bg-tertiary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-primary)',
    borderRadius: '6px',
    padding: '12px 16px',
    fontSize: '14px',
    width: '100%',
    transition: 'all 0.3s ease'
  };

  const selectStyle: React.CSSProperties = {
    backgroundColor: 'var(--bg-tertiary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-primary)',
    borderRadius: '6px',
    padding: '12px 16px',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.3s ease'
  };

  return (
    <div style={{
      padding: '24px',
      backgroundColor: 'var(--bg-primary)',
      minHeight: '100vh',
      color: 'var(--text-primary)'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '32px',
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: '32px',
          fontWeight: '700',
          color: 'var(--text-primary)',
          marginBottom: '8px'
        }}>
          🕷️ AI-Powered Web Scraper
        </h1>
        <p style={{
          fontSize: '16px',
          color: 'var(--text-secondary)',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          Extract data from websites with intelligent AI assistance. Configure your scraping parameters and let our AI handle the complex extraction logic.
        </p>
      </div>

      {/* Progress Steps */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '32px',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {steps.map((step, index) => (
          <div
            key={step.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '12px 20px',
              backgroundColor: step.active ? 'var(--accent-primary)' : step.completed ? 'var(--success)' : 'var(--bg-secondary)',
              color: step.active || step.completed ? 'var(--white)' : 'var(--text-secondary)',
              borderRadius: '25px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              border: `2px solid ${step.active ? 'var(--accent-primary)' : step.completed ? 'var(--success)' : 'var(--border-primary)'}`
            }}
            onClick={() => setCurrentStep(step.id)}
          >
            {step.completed && '✅ '}
            {step.title}
          </div>
        ))}
      </div>

      {/* Step 1: URL & Target Setup */}
      {currentStep === 1 && (
        <div style={stepContainerStyle}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            🎯 Target Website Setup
          </h2>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '8px'
            }}>
              Website URL *
            </label>
            <input
              type="url"
              placeholder="https://example.com/products"
              value={config.url}
              onChange={(e) => setConfig(prev => ({ ...prev, url: e.target.value }))}
              style={inputStyle}
            />
            <p style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              marginTop: '4px'
            }}>
              Enter the URL of the website you want to scrape
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '16px'
            }}>
              Quick Templates
            </h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px'
            }}>
              {sampleTemplates.map((template, index) => (
                <div
                  key={index}
                  onClick={() => handleTemplateSelect(template)}
                  style={{
                    padding: '16px',
                    backgroundColor: 'var(--bg-tertiary)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-primary)',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-hover)';
                    e.currentTarget.style.borderColor = 'var(--accent-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                    e.currentTarget.style.borderColor = 'var(--border-primary)';
                  }}
                >
                  <h4 style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}>
                    {template.name}
                  </h4>
                  <p style={{
                    fontSize: '14px',
                    color: 'var(--text-secondary)',
                    marginBottom: '12px'
                  }}>
                    {template.description}
                  </p>
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '4px'
                  }}>
                    {template.attributes.slice(0, 3).map((attr, i) => (
                      <span
                        key={i}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: 'var(--accent-primary)',
                          color: 'var(--accent-text)',
                          fontSize: '12px',
                          borderRadius: '12px',
                          fontWeight: '500'
                        }}
                      >
                        {attr}
                      </span>
                    ))}
                    {template.attributes.length > 3 && (
                      <span style={{
                        padding: '4px 8px',
                        backgroundColor: 'var(--bg-secondary)',
                        color: 'var(--text-muted)',
                        fontSize: '12px',
                        borderRadius: '12px'
                      }}>
                        +{template.attributes.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setCurrentStep(2)}
              disabled={!config.url}
              style={{
                ...buttonStyle,
                opacity: config.url ? 1 : 0.5,
                cursor: config.url ? 'pointer' : 'not-allowed'
              }}
            >
              Next: Configure Attributes →
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Configure Attributes */}
      {currentStep === 2 && (
        <div style={stepContainerStyle}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            🔧 Data Attributes Configuration
          </h2>

          <div style={{ marginBottom: '24px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px'
            }}>
              <label style={{
                fontSize: '16px',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>
                Attributes to Extract
              </label>
              <button
                onClick={addAttribute}
                style={{
                  ...buttonStyle,
                  fontSize: '12px',
                  padding: '8px 16px'
                }}
              >
                + Add Attribute
              </button>
            </div>

            <div style={{
              display: 'grid',
              gap: '12px'
            }}>
              {config.attributes.map((attr, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    gap: '12px',
                    alignItems: 'center'
                  }}
                >
                  <input
                    type="text"
                    placeholder="e.g., title, price, description"
                    value={attr}
                    onChange={(e) => updateAttribute(index, e.target.value)}
                    style={{
                      ...inputStyle,
                      flex: 1
                    }}
                  />
                  <button
                    onClick={() => removeAttribute(index)}
                    style={{
                      backgroundColor: 'var(--error)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '12px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>

            {config.attributes.length === 0 && (
              <div style={{
                padding: '32px',
                backgroundColor: 'var(--bg-tertiary)',
                borderRadius: '8px',
                textAlign: 'center',
                border: '2px dashed var(--border-primary)'
              }}>
                <p style={{
                  color: 'var(--text-muted)',
                  fontSize: '14px'
                }}>
                  No attributes configured. Add attributes to extract from the target website.
                </p>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button
              onClick={() => setCurrentStep(1)}
              style={{
                ...buttonStyle,
                backgroundColor: 'var(--bg-tertiary)',
                color: 'var(--text-primary)'
              }}
            >
              ← Back
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              disabled={config.attributes.length === 0 || config.attributes.some(attr => !attr.trim())}
              style={{
                ...buttonStyle,
                opacity: (config.attributes.length > 0 && !config.attributes.some(attr => !attr.trim())) ? 1 : 0.5,
                cursor: (config.attributes.length > 0 && !config.attributes.some(attr => !attr.trim())) ? 'pointer' : 'not-allowed'
              }}
            >
              Next: Configure Filters →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Filters & Pages */}
      {currentStep === 3 && (
        <div style={stepContainerStyle}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            ⚙️ Filters & Pagination Settings
          </h2>

          {/* Page Limit Setting */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'block',
              fontSize: '16px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '12px'
            }}>
              🔢 Number of Pages to Scrape
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <input
                type="range"
                min="1"
                max="100"
                value={config.maxPages}
                onChange={(e) => setConfig(prev => ({ ...prev, maxPages: parseInt(e.target.value) }))}
                style={{
                  flex: 1,
                  height: '6px',
                  backgroundColor: 'var(--bg-tertiary)',
                  borderRadius: '3px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              />
              <div style={{
                backgroundColor: 'var(--accent-primary)',
                color: 'var(--accent-text)',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '14px',
                fontWeight: '600',
                minWidth: '80px',
                textAlign: 'center'
              }}>
                {config.maxPages} pages
              </div>
            </div>
            <p style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              marginTop: '8px'
            }}>
              Specify how many pages to scrape. Higher values may take longer to complete.
            </p>
          </div>

          {/* Request Delay Setting */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'block',
              fontSize: '16px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '12px'
            }}>
              ⏱️ Request Delay (milliseconds)
            </label>
            <select
              value={config.requestDelay}
              onChange={(e) => setConfig(prev => ({ ...prev, requestDelay: parseInt(e.target.value) }))}
              style={selectStyle}
            >
              <option value={500}>500ms - Fast (may trigger rate limits)</option>
              <option value={1000}>1000ms - Balanced (recommended)</option>
              <option value={2000}>2000ms - Conservative</option>
              <option value={5000}>5000ms - Very slow (safest)</option>
            </select>
          </div>

          {/* Filters Configuration */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px'
            }}>
              <label style={{
                fontSize: '16px',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>
                🔍 Page Interaction Filters (Optional)
              </label>
              <button
                onClick={addFilter}
                style={{
                  ...buttonStyle,
                  fontSize: '12px',
                  padding: '8px 16px'
                }}
              >
                + Add Filter
              </button>
            </div>

            {config.filters.length > 0 ? (
              <div style={{ display: 'grid', gap: '16px' }}>
                {config.filters.map((filter, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '16px',
                      backgroundColor: 'var(--bg-tertiary)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-primary)'
                    }}
                  >
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 1fr auto',
                      gap: '12px',
                      alignItems: 'end'
                    }}>
                      <div>
                        <label style={{
                          display: 'block',
                          fontSize: '12px',
                          fontWeight: '500',
                          color: 'var(--text-secondary)',
                          marginBottom: '4px'
                        }}>
                          CSS Selector
                        </label>
                        <input
                          type="text"
                          placeholder=".filter-button, #search-input"
                          value={filter.selector}
                          onChange={(e) => updateFilter(index, 'selector', e.target.value)}
                          style={inputStyle}
                        />
                      </div>
                      <div>
                        <label style={{
                          display: 'block',
                          fontSize: '12px',
                          fontWeight: '500',
                          color: 'var(--text-secondary)',
                          marginBottom: '4px'
                        }}>
                          Action
                        </label>
                        <select
                          value={filter.action}
                          onChange={(e) => updateFilter(index, 'action', e.target.value)}
                          style={selectStyle}
                        >
                          <option value="click">Click</option>
                          <option value="input">Type Text</option>
                          <option value="select">Select Option</option>
                        </select>
                      </div>
                      <div>
                        <label style={{
                          display: 'block',
                          fontSize: '12px',
                          fontWeight: '500',
                          color: 'var(--text-secondary)',
                          marginBottom: '4px'
                        }}>
                          Value
                        </label>
                        <input
                          type="text"
                          placeholder={filter.action === 'click' ? '(no value needed)' : 'Enter value...'}
                          value={filter.value}
                          onChange={(e) => updateFilter(index, 'value', e.target.value)}
                          style={inputStyle}
                          disabled={filter.action === 'click'}
                        />
                      </div>
                      <button
                        onClick={() => removeFilter(index)}
                        style={{
                          backgroundColor: 'var(--error)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '12px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '24px',
                backgroundColor: 'var(--bg-tertiary)',
                borderRadius: '8px',
                textAlign: 'center',
                border: '2px dashed var(--border-primary)'
              }}>
                <p style={{
                  color: 'var(--text-muted)',
                  fontSize: '14px'
                }}>
                  No filters configured. Add filters to interact with page elements before scraping.
                </p>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button
              onClick={() => setCurrentStep(2)}
              style={{
                ...buttonStyle,
                backgroundColor: 'var(--bg-tertiary)',
                color: 'var(--text-primary)'
              }}
            >
              ← Back
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              style={buttonStyle}
            >
              Next: Preview & Export →
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Preview & Export */}
      {currentStep === 4 && (
        <div style={stepContainerStyle}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            📊 Preview & Export Configuration
          </h2>

          {/* Output Format Selection */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{
              display: 'block',
              fontSize: '16px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '12px'
            }}>
              📂 Export Format
            </label>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              {[
                { key: 'gsheets', label: '📊 Google Sheets', desc: 'Live collaborative spreadsheet' },
                { key: 'csv', label: '📄 CSV File', desc: 'Comma-separated values' },
                { key: 'json', label: '🔧 JSON File', desc: 'Structured data format' }
              ].map(format => (
                <div
                  key={format.key}
                  onClick={() => setConfig(prev => ({ ...prev, outputFormat: format.key as any }))}
                  style={{
                    padding: '16px',
                    backgroundColor: config.outputFormat === format.key ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    color: config.outputFormat === format.key ? 'var(--accent-text)' : 'var(--text-primary)',
                    borderRadius: '8px',
                    border: `2px solid ${config.outputFormat === format.key ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    textAlign: 'center'
                  }}
                >
                  <div style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    marginBottom: '8px'
                  }}>
                    {format.label}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    opacity: 0.8
                  }}>
                    {format.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Google Sheets Path */}
          {config.outputFormat === 'gsheets' && (
            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'block',
                fontSize: '16px',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '8px'
              }}>
                🔗 Google Sheets Configuration
              </label>
              <input
                type="text"
                placeholder="Spreadsheet Name (e.g., 'Web Scraping Results')"
                value={config.gsheetsPath || ''}
                onChange={(e) => setConfig(prev => ({ ...prev, gsheetsPath: e.target.value }))}
                style={inputStyle}
              />
              <p style={{
                fontSize: '12px',
                color: 'var(--text-muted)',
                marginTop: '4px'
              }}>
                A new Google Sheets document will be created with this name
              </p>
            </div>
          )}

          {/* Preview Section */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px'
            }}>
              <h3 style={{
                fontSize: '18px',
                fontWeight: '600',
                color: 'var(--text-primary)'
              }}>
                📋 Data Preview
              </h3>
              <button
                onClick={generatePreview}
                disabled={isLoading}
                style={{
                  ...buttonStyle,
                  fontSize: '12px',
                  padding: '8px 16px',
                  opacity: isLoading ? 0.7 : 1,
                  cursor: isLoading ? 'not-allowed' : 'pointer'
                }}
              >
                {isLoading ? '🔄 Generating...' : '🔄 Generate Preview'}
              </button>
            </div>

            {previewData.length > 0 ? (
              <div style={{
                backgroundColor: 'var(--bg-tertiary)',
                borderRadius: '8px',
                border: '1px solid var(--border-primary)',
                overflow: 'hidden'
              }}>
                <div style={{
                  overflowX: 'auto'
                }}>
                  <table style={{
                    width: '100%',
                    borderCollapse: 'collapse'
                  }}>
                    <thead>
                      <tr style={{
                        backgroundColor: 'var(--bg-secondary)'
                      }}>
                        {config.attributes.map(attr => (
                          <th
                            key={attr}
                            style={{
                              padding: '16px',
                              textAlign: 'left',
                              fontSize: '12px',
                              fontWeight: '600',
                              color: 'var(--text-secondary)',
                              textTransform: 'uppercase',
                              letterSpacing: '1px',
                              borderBottom: '1px solid var(--border-primary)'
                            }}
                          >
                            {attr}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.map((row, index) => (
                        <tr
                          key={index}
                          style={{
                            borderBottom: '1px solid var(--border-primary)'
                          }}
                        >
                          {config.attributes.map(attr => (
                            <td
                              key={attr}
                              style={{
                                padding: '16px',
                                fontSize: '14px',
                                color: 'var(--text-primary)'
                              }}
                            >
                              {row[attr] || '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div style={{
                padding: '48px',
                backgroundColor: 'var(--bg-tertiary)',
                borderRadius: '8px',
                textAlign: 'center',
                border: '2px dashed var(--border-primary)'
              }}>
                <p style={{
                  color: 'var(--text-muted)',
                  fontSize: '16px',
                  marginBottom: '8px'
                }}>
                  🔍 No preview data available
                </p>
                <p style={{
                  color: 'var(--text-muted)',
                  fontSize: '14px'
                }}>
                  Click "Generate Preview" to see a sample of the data that will be extracted
                </p>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button
              onClick={() => setCurrentStep(3)}
              style={{
                ...buttonStyle,
                backgroundColor: 'var(--bg-tertiary)',
                color: 'var(--text-primary)'
              }}
            >
              ← Back
            </button>
            <button
              onClick={startScraping}
              style={buttonStyle}
            >
              🚀 Start Scraping
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Execute Scraping */}
      {currentStep === 5 && (
        <div style={stepContainerStyle}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            🚀 Scraping in Progress
          </h2>

          <div style={{
            textAlign: 'center',
            marginBottom: '32px'
          }}>
            <div style={{
              width: '100%',
              backgroundColor: 'var(--bg-tertiary)',
              borderRadius: '10px',
              overflow: 'hidden',
              marginBottom: '16px'
            }}>
              <div
                style={{
                  height: '20px',
                  backgroundColor: 'var(--accent-primary)',
                  borderRadius: '10px',
                  width: `${progress}%`,
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
            <p style={{
              fontSize: '18px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '8px'
            }}>
              {progress < 100 ? `Scraping in progress... ${Math.round(progress)}%` : 'Scraping completed! 🎉'}
            </p>
            <p style={{
              fontSize: '14px',
              color: 'var(--text-secondary)'
            }}>
              {progress < 100 
                ? `Processing ${config.url} - ${Math.ceil(progress / 100 * config.maxPages)} of ${config.maxPages} pages`
                : `Successfully scraped ${config.maxPages} pages and extracted data to ${config.outputFormat}`
              }
            </p>
          </div>

          {progress >= 100 && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '16px'
            }}>
              <button
                onClick={() => {
                  setCurrentStep(1);
                  setProgress(0);
                  setPreviewData([]);
                }}
                style={{
                  ...buttonStyle,
                  backgroundColor: 'var(--bg-tertiary)',
                  color: 'var(--text-primary)'
                }}
              >
                🔄 Start New Scraping
              </button>
              <button
                style={buttonStyle}
              >
                📊 View Results
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};