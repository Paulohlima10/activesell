class EventFlowManager:
    def __init__(self):
        self.state = {}

    def handle_event(self, event_name, payload=None):
        print(f"[EVENTO] Recebido: {event_name}")

        match event_name:
            case "start_import":
                self.import_data()
            case "data_imported":
                self.analyze_data()
            case "data_analyzed":
                self.generate_offers()
            case "offers_generated":
                self.send_campaign()
            case "campaign_sent":
                self.activate_agents()
            case _:
                print(f"Evento desconhecido: {event_name}")

    def import_data(self):
        print("Importando dados do banco do cliente...")
        # Simula importação
        self.handle_event("data_imported")

    def analyze_data(self):
        print("Analisando dados de compra e comportamento...")
        # Simula análise
        self.handle_event("data_analyzed")

    def generate_offers(self):
        print("Gerando ofertas personalizadas...")
        # Simula geração
        self.handle_event("offers_generated")

    def send_campaign(self):
        print("Enviando campanha via WhatsApp...")
        # Simula envio
        self.handle_event("campaign_sent")

    def activate_agents(self):
        print("Ativando agentes de IA para interação com clientes...")
        # Simula ativação
        print("Fluxo finalizado.")


# Executa o fluxo
if __name__ == "__main__":
    flow = EventFlowManager()
    flow.handle_event("start_import")
