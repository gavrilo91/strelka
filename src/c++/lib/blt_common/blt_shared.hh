// -*- mode: c++; indent-tabs-mode: nil; -*-
//
// Strelka - Small Variant Caller
// Copyright (c) 2009-2016 Illumina, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//

///
/// \author Chris Saunders
///

#pragma once

#include "blt_util/blt_types.hh"
#include "blt_util/pos_range.hh"
#include "blt_util/seq_util.hh"

#include <cassert>

#include <memory>
#include <vector>

extern const char STDIN_FILENAME[];

extern const unsigned MAX_FLANK_SIZE;


namespace LOG_LEVEL
{
enum index_t
{
    DEFAULT = 0, // 0 = errors and low-frequency warnings
    ALLWARN = 1  // all other warnings
};
}



struct blt_options
{
    blt_options() {}
    virtual ~blt_options() {}

    void
    validate() const
    {
        // this should never be true, TODO: can we move this into a state enum so it *can't* be true:
        assert(! (is_compute_germline_scoring_metrics() && is_compute_somatic_scoring_metrics));
    }

    bool
    is_ref_set() const
    {
        return (is_samtools_ref_set);
    }

    virtual
    bool
    is_compute_germline_scoring_metrics() const
    {
        return false;
    }

    virtual
    bool
    is_bsnp_diploid() const
    {
        return false;
    }

    bool
    is_dependent_eprob() const
    {
        return (is_bsnp_diploid() &&
                (bsnp_ssd_no_mismatch>0. || bsnp_ssd_one_mismatch>0));
    }

    double lsnp_alpha = 0;
    double bsnp_diploid_theta = 0.001;
    int bsnp_nploid_ploidy = 0;
    double bsnp_nploid_snp_prob = 0;
    double bsnp_ssd_no_mismatch = 0;
    double bsnp_ssd_one_mismatch = 0;
    double bsnp_diploid_het_bias = 0;

    bool is_lsnp = false;
    bool is_bsnp_nploid = false;
    bool is_bsnp_diploid_het_bias = false;

    int min_qscore = 17;
    int min_mapping_quality = 20;

    bool is_max_win_mismatch = false;
    unsigned max_win_mismatch = 0;
    unsigned max_win_mismatch_flank_size = 0;
    bool is_counts = false;
    bool is_print_evidence = false;
    bool is_print_all_site_evidence = false;
    pos_range user_report_range;   // requested report range

    bool is_samtools_ref_set = false;
    std::string samtools_ref_seq_file;

    bool is_include_singleton = false;
    bool is_include_anomalous = false;

    std::string counts_filename;

    bool is_report_range_ref = false;
    int used_allele_count_min_qscore = 0; // print the above with a qscore cutoff...

    int max_vexp_iterations = 0;
    bool is_min_vexp = false;
    double min_vexp = 0;

    LOG_LEVEL::index_t verbosity = LOG_LEVEL::DEFAULT;

    bool is_write_variable_metadata = true;

    std::string cmdline;

    // constants for het-bias model:
    //
    // Humans will often pick exact multples of the max_ratio increment,
    // which are also the least efficient points in terms of increment
    // size -- fudge removes this trend from the computation:
    //
    const double het_bias_inc_fudge = 0.0001;
    const double het_bias_max_ratio_inc = 0.05 + het_bias_inc_fudge;

    bool is_max_input_depth = false;
    unsigned max_input_depth = 0;

    bool is_compute_hapscore = false;
    bool isReportEVSFeatures = false;
    bool is_compute_somatic_scoring_metrics = false;

    std::string report_filename;
};



struct pprob_digt_caller;


// data deterministically derived from the user input options:
//
struct blt_deriv_options
{
    /// @param ref_end this is either the full reference contig size,
    /// or the end position of the acquired reference segment if
    /// -report-range-end was used
    ///
    blt_deriv_options(
        const blt_options& opt,
        const pos_t ref_end);

    ~blt_deriv_options();

    pos_range report_range;
    pos_range report_range_limit;   //  maximum report range

    const pprob_digt_caller&
    pdcaller() const
    {
        return *(_pdcaller.get());
    }

private:
    std::unique_ptr<pprob_digt_caller> _pdcaller; // object to precalculate bsnp_diploid priors..
};



struct blt_read_counts
{
    void
    report(std::ostream& os) const;

    unsigned subsample_filter = 0;
    unsigned primary_filter = 0;
    unsigned duplicate = 0;
    unsigned unmapped = 0;
    unsigned secondary = 0;
    unsigned supplement = 0;
    unsigned unanchored = 0;
    unsigned large_ref_deletion = 0;
    unsigned align_score_filter = 0;

    // Floating means the read is indicated as mapped, but has no "M"
    // in the cigar string. Typically inside of an insertion.
    unsigned floating = 0;

    // if optional setting is given to filter out reads once a certain depth
    // is exceeded, the number of reads filtered are enumerated here:
    unsigned max_depth = 0;
    unsigned used = 0;
};
