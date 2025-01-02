# Order Fulfillment AI

An educational project exploring the use of AI for order fulfillment automation. This project demonstrates how to use different AI models for planning and execution, testing plans against various business contexts.

## 🎓 Educational Purpose

This project is designed to help developers learn:
- Separation of planning and execution in AI systems
- Testing AI-generated plans across different contexts
- Integration of multiple AI models (O1 for planning, GPT-4 for execution)
- Business logic implementation and context management
- Proper project structure and documentation
- Type hinting and modern Python practices

## 🚀 Getting Started

1. Clone the repository
git clone https://github.com/yourusername/order-fulfillment-ai.git
cd order-fulfillment-ai


2. Create and activate a virtual environment

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Set up your environment variables
cp .env.example .env
Edit .env with your OpenAI API key

## 📊 Key Features

### Plan Generation and Execution
- Generate plans using O1-mini model
- Execute plans using GPT-4
- Save and reuse generated plans
- Test plans against different business contexts

### Configurable Components
- **Contexts**: Test scenarios with different inventory levels, warehouse capacities, etc.
- **Models**: Swap between different AI models for planning and execution
- **Scenarios**: Define and test various business scenarios
- **Business Functions**: Extensible set of operations for order processing

## 🔧 Usage Examples

### Running Comprehensive Experiments

## 📊 Available Scenarios
- **Basic Fulfillment**: Process orders with standard inventory management
- **Low Inventory**: Handle orders when stock is limited
- **Supplier Optimization**: Choose optimal supplier based on costs and constraints

## 🔄 Available Contexts
- **Default**: Standard operating conditions
- **Low Inventory**: Limited stock levels
- **High Capacity**: Increased warehouse processing capacity

## 📖 Documentation
See the [docs](docs/) directory for detailed documentation:
- [API Documentation](docs/API.md)
- [Function Registry](docs/function_registry.md)

## 🤝 Contributing
This is an educational project and contributions that help make it more educational are welcome! Please feel free to:
- Add new scenarios
- Create additional contexts
- Improve documentation
- Add test cases
- Suggest improvements

## ⚠️ Disclaimer
This is an educational project and should not be used in production environments without significant modifications and proper error handling.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📁 Project Structure
order-fulfillment-ai/
├── src/prototype/order_fulfillment/
│ ├── config.py # Model and prompt configurations
│ ├── context.py # Context management
│ ├── executor.py # Execution engine
│ ├── functions.py # Business functions
│ ├── plans.py # Plan management
│ ├── scenarios.py # Scenario definitions
│ └── utils.py # Utilities
├── run_results/
│ ├── plans/ # Stored plans
│ └── fulfillment_runs/ # Execution logs
