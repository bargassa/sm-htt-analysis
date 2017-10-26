#!/usr/bin/env python
# -*- coding: utf-8 -*-

import CombineHarvester.CombineTools.ch as ch
from datacard_producer.datacard_builder import DatacardBuilder

import argparse

import logging
logger = logging.getLogger("")


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Produce datacards for 2016 Standard Model analysis.")

    parser.add_argument(
        "--shapes",
        default="shapes.root",
        type=str,
        help="Nominal shapes and systematic variations.")

    return parser.parse_args()


def main(args):
    db = DatacardBuilder(args.shapes)

    # Register observations, signals and backgrounds
    mt_categories = [
        "mt_Htt", "mt_Ztt", "mt_Zll", "mt_WJets", "mt_tt", "mt_QCD"
    ]
    mt_category_pairs = db.make_pairs(mt_categories)

    db.add_observation("125", "smhtt", "Run2016", "mt", mt_category_pairs)

    signals = ["Htt"]
    db.add_signals("125", "smhtt", "Run2016", "mt", signals, mt_category_pairs)

    backgrounds = ["Ztt", "Zll", "WJets", "VV", "tt", "QCD"]
    db.add_backgrounds("125", "smhtt", "Run2016", "mt", backgrounds,
                       mt_category_pairs)

    # Add shapes systematics
    db.add_shape_systematic("CMS_scale_t_3prong0pi0", 1.0, "mt",
                            ["Htt", "Ztt"])
    db.add_shape_systematic("CMS_scale_t_1prong0pi0", 1.0, "mt",
                            ["Htt", "Ztt"])
    db.add_shape_systematic("CMS_scale_t_1prong1pi0", 1.0, "mt",
                            ["Htt", "Ztt"])
    db.add_shape_systematic("CMS_htt_dyShape", 1.0, "mt", ["Ztt", "Zll"])

    # Add normalization systematics
    db.add_normalization_systematic("lumi_13TeV", 1.026, "mt",
                                    signals + backgrounds)
    db.add_normalization_systematic("CMS_eff_m", 1.02, "mt",
                                    signals + backgrounds)
    db.add_normalization_systematic("CMS_eff_trigger_mt", 1.02, "mt",
                                    signals + backgrounds)
    db.add_normalization_systematic("CMS_Extrap_SSOS_mt", 1.20, "mt", "QCD")
    db.add_normalization_systematic("CMS_htt_wjXsec", 1.04, "mt", "WJets")
    db.add_normalization_systematic("CMS_htt_vvXsec", 1.06, "mt", "VV")
    # TODO: tt and z normalizations
    """
    db.add_normalization_systematic("CMS_htt_ttXsec", 1.00, "mt", "tt")
    db.add_normalization_systematic("CMS_htt_zXsec", 1.00, "mt", ["Ztt", "Zll"])
    """

    # Extract shapes
    db.extract_shapes("mt", "smhtt", "Run2016", "mt_keras2_max_score")

    # Replace observation with Asimov dataset
    db.replace_observation_by_asimov_dataset()

    # Add bin-by-bin systematics
    db.add_bin_by_bin_systematics(
        signals + backgrounds,
        add_threshold=0.1,
        merge_threshold=0.5,
        fix_norm=True)

    # Perform auto-rebinning
    db.auto_rebin(threshold=1.0, mode=0)

    # Write datacard
    db.print_datacard()
    db.write("datacard.txt", "datacard_shapes.root")


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("produce_datacard.log", logging.DEBUG)
    main(args)