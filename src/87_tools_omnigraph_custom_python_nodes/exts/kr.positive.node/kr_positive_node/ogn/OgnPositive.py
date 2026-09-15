class OgnPositive:
    @staticmethod
    def compute(db):
        db.outputs.output_bool = db.inputs.value_input > 0.0
        return True
