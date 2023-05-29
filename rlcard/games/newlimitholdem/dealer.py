from rlcard.utils.utils import init_20_deck


class NewLimitHoldemDealer:
    def __init__(self, np_random):
        self.np_random = np_random
        self.deck = init_20_deck()
        self.shuffle()
        self.pot = 0

    def shuffle(self):
        self.np_random.shuffle(self.deck)

    def deal_card(self):
        """
        Deal one card from the deck

        Returns:
            (Card): The drawn card from the deck
        """
        return self.deck.pop()
